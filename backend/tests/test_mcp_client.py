from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.auth.mcp_client import BinanceMCPClient
from app.core.exceptions import BinanceAuthRequiredError


class TestMCPClient:
    @pytest.mark.asyncio
    async def test_get_headers_raises_when_no_token(self) -> None:
        client = BinanceMCPClient()
        mock_session = AsyncMock()
        with patch("app.auth.mcp_client.binance_oauth_service") as mock_service:
            mock_service.get_valid_token = AsyncMock(return_value=None)
            with pytest.raises(BinanceAuthRequiredError):
                await client._get_headers(mock_session, "user-123")

    @pytest.mark.asyncio
    async def test_get_headers_returns_auth_header(self) -> None:
        client = BinanceMCPClient()
        mock_session = AsyncMock()
        with patch("app.auth.mcp_client.binance_oauth_service") as mock_service:
            mock_service.get_valid_token = AsyncMock(return_value="test_token")
            headers = await client._get_headers(mock_session, "user-123")
            assert headers["Authorization"] == "Bearer test_token"

    @pytest.mark.asyncio
    async def test_send_request_raises_on_401(self) -> None:
        client = BinanceMCPClient()
        mock_session = AsyncMock()

        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"

        with patch("app.auth.mcp_client.binance_oauth_service") as mock_service:
            mock_service.get_valid_token = AsyncMock(return_value="test_token")
            mock_service.refresh_token = AsyncMock(return_value=False)
            with patch.object(client._client, "post", new_callable=AsyncMock, return_value=mock_response):
                with pytest.raises(BinanceAuthRequiredError):
                    await client._send_request(mock_session, "user-123", "test")

    def test_next_id_increments(self) -> None:
        client = BinanceMCPClient()
        assert client._next_id() == 1
        assert client._next_id() == 2

    @pytest.mark.asyncio
    async def test_initialize_sends_correct_payload(self) -> None:
        client = BinanceMCPClient()
        mock_session = AsyncMock()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "protocolVersion": "2025-03-26",
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "binance-mcp", "version": "1.0.0"},
            },
        }
        mock_response.raise_for_status = MagicMock()

        with patch("app.auth.mcp_client.binance_oauth_service") as mock_service:
            mock_service.get_valid_token = AsyncMock(return_value="test_token")
            with patch.object(client._client, "post", new_callable=AsyncMock, return_value=mock_response) as mock_post:
                result = await client.initialize(mock_session, "user-123")
                assert "protocolVersion" in result
                call_args = mock_post.call_args
                payload = call_args.kwargs.get("json") or call_args[1].get("json")
                assert payload["method"] == "initialize"

    @pytest.mark.asyncio
    async def test_list_tools_returns_tools(self) -> None:
        client = BinanceMCPClient()
        mock_session = AsyncMock()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "tools": [
                    {"name": "get_price", "description": "Get price", "inputSchema": {}},
                    {"name": "get_klines", "description": "Get klines", "inputSchema": {}},
                ]
            },
        }
        mock_response.raise_for_status = MagicMock()

        with patch("app.auth.mcp_client.binance_oauth_service") as mock_service:
            mock_service.get_valid_token = AsyncMock(return_value="test_token")
            with patch.object(client._client, "post", new_callable=AsyncMock, return_value=mock_response):
                tools = await client.list_tools(mock_session, "user-123")
                assert len(tools) == 2
                assert tools[0]["name"] == "get_price"

    @pytest.mark.asyncio
    async def test_call_tool(self) -> None:
        client = BinanceMCPClient()
        mock_session = AsyncMock()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "content": [{"type": "text", "text": "BTC price: $60000"}],
            },
        }
        mock_response.raise_for_status = MagicMock()

        with patch("app.auth.mcp_client.binance_oauth_service") as mock_service:
            mock_service.get_valid_token = AsyncMock(return_value="test_token")
            with patch.object(client._client, "post", new_callable=AsyncMock, return_value=mock_response):
                result = await client.call_tool(mock_session, "user-123", "get_price", {"symbol": "BTCUSDT"})
                assert "content" in result

    @pytest.mark.asyncio
    async def test_mcp_error_raises_value_error(self) -> None:
        client = BinanceMCPClient()
        mock_session = AsyncMock()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "id": 1,
            "error": {"code": -32601, "message": "Method not found"},
        }
        mock_response.raise_for_status = MagicMock()

        with patch("app.auth.mcp_client.binance_oauth_service") as mock_service:
            mock_service.get_valid_token = AsyncMock(return_value="test_token")
            with patch.object(client._client, "post", new_callable=AsyncMock, return_value=mock_response):
                with pytest.raises(ValueError, match="MCP error"):
                    await client.initialize(mock_session, "user-123")
