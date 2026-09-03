import json
import logging
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.binance_oauth import binance_oauth_service
from app.core.config import get_settings
from app.core.exceptions import BinanceAuthRequiredError

logger = logging.getLogger(__name__)


class BinanceMCPClient:
    """Multi-user Binance MCP client. Operates on behalf of a specific user."""

    def __init__(self) -> None:
        self._client = httpx.AsyncClient(timeout=30.0)
        self._request_id = 0

    def _next_id(self) -> int:
        self._request_id += 1
        return self._request_id

    async def _get_headers(self, session: AsyncSession, user_id: str) -> dict[str, str]:
        token = await binance_oauth_service.get_valid_token(session, user_id)
        if token is None:
            raise BinanceAuthRequiredError()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def _send_request(
        self,
        session: AsyncSession,
        user_id: str,
        method: str,
        params: dict[str, Any] | None = None,
    ) -> dict:
        settings = get_settings()
        headers = await self._get_headers(session, user_id)

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

        # Handle 401: try refresh + one retry
        if resp.status_code == 401:
            refreshed = await binance_oauth_service.get_valid_token(session, user_id)
            if refreshed:
                headers["Authorization"] = f"Bearer {refreshed}"
                resp = await self._client.post(
                    settings.binance_mcp_url,
                    json=payload,
                    headers=headers,
                )

            if resp.status_code == 401:
                raise BinanceAuthRequiredError()

        resp.raise_for_status()
        result = resp.json()

        if "error" in result:
            error = result["error"]
            raise ValueError(f"MCP error {error.get('code')}: {error.get('message')}")

        return result.get("result", {})

    async def initialize(self, session: AsyncSession, user_id: str) -> dict:
        return await self._send_request(session, user_id, "initialize", {
            "protocolVersion": "2025-03-26",
            "capabilities": {},
            "clientInfo": {"name": "binance-agent-os-backend", "version": "0.1.0"},
        })

    async def list_tools(self, session: AsyncSession, user_id: str) -> list[dict]:
        result = await self._send_request(session, user_id, "tools/list")
        return result.get("tools", [])

    async def call_tool(
        self,
        session: AsyncSession,
        user_id: str,
        name: str,
        arguments: dict[str, Any],
    ) -> Any:
        result = await self._send_request(session, user_id, "tools/call", {
            "name": name,
            "arguments": arguments,
        })
        return result

    async def close(self) -> None:
        await self._client.aclose()


mcp_client = BinanceMCPClient()
