import json
import logging
from typing import Any

import httpx

from app.auth.oauth import binance_oauth
from app.auth.token_store import token_store
from app.core.config import get_settings
from app.core.exceptions import BinanceAuthRequiredError

logger = logging.getLogger(__name__)


class BinanceMCPClient:
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(timeout=30.0)
        self._request_id = 0

    def _next_id(self) -> int:
        self._request_id += 1
        return self._request_id

    async def _get_headers(self) -> dict[str, str]:
        token = await token_store.get()
        if token is None:
            raise BinanceAuthRequiredError()

        if token.is_expired and token.refresh_token:
            refreshed = await binance_oauth.refresh_access_token(token.refresh_token)
            if refreshed is None:
                raise BinanceAuthRequiredError()
            token = refreshed

        return {
            "Authorization": f"Bearer {token.access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def _send_request(self, method: str, params: dict[str, Any] | None = None) -> dict:
        settings = get_settings()
        headers = await self._get_headers()

        payload = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": method,
        }
        if params:
            payload["params"] = params

        resp = await self._client.post(
            settings.binance_mcp_url,
            json=payload,
            headers=headers,
        )

        if resp.status_code == 401:
            token = await token_store.get()
            if token and token.refresh_token:
                refreshed = await binance_oauth.refresh_access_token(token.refresh_token)
                if refreshed:
                    headers["Authorization"] = f"Bearer {refreshed.access_token}"
                    resp = await self._client.post(
                        settings.binance_mcp_url,
                        json=payload,
                        headers=headers,
                    )

            if resp.status_code == 401:
                await token_store.delete()
                raise BinanceAuthRequiredError()

        resp.raise_for_status()
        result = resp.json()

        if "error" in result:
            error = result["error"]
            raise ValueError(f"MCP error {error.get('code')}: {error.get('message')}")

        return result.get("result", {})

    async def initialize(self) -> dict:
        return await self._send_request("initialize", {
            "protocolVersion": "2025-03-26",
            "capabilities": {},
            "clientInfo": {"name": "binance-agent-os-backend", "version": "0.1.0"},
        })

    async def list_tools(self) -> list[dict]:
        result = await self._send_request("tools/list")
        return result.get("tools", [])

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        result = await self._send_request("tools/call", {
            "name": name,
            "arguments": arguments,
        })
        return result

    async def close(self) -> None:
        await self._client.aclose()


mcp_client = BinanceMCPClient()
