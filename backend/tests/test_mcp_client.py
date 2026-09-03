from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.auth.mcp_client import BinanceMCPClient
from app.auth.token_store import TokenData
from app.core.exceptions import BinanceAuthRequiredError


class TestMCPClient:
    @pytest.mark.asyncio
    async def test_get_headers_raises_when_no_token(self) -> None:
        client = BinanceMCPClient()
        with patch("app.auth.mcp_client.token_store") as mock_store:
            mock_store.get = AsyncMock(return_value=None)
            with pytest.raises(BinanceAuthRequiredError):
                await client._get_headers()

    @pytest.mark.asyncio
    async def test_get_headers_returns_auth_header(self) -> None:
        client = BinanceMCPClient()
        token = TokenData(access_token="test_token", expires_at=9999999999)
        with patch("app.auth.mcp_client.token_store") as mock_store:
            mock_store.get = AsyncMock(return_value=token)
            headers = await client._get_headers()
            assert headers["Authorization"] == "Bearer test_token"

    @pytest.mark.asyncio
    async def test_send_request_raises_on_401(self) -> None:
        client = BinanceMCPClient()
        token = TokenData(access_token="test", expires_at=9999999999)

        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"

        with patch("app.auth.mcp_client.token_store") as mock_store:
            mock_store.get = AsyncMock(return_value=token)
            mock_store.delete = AsyncMock()
            with patch.object(client._client, "post", new_callable=AsyncMock, return_value=mock_response):
                with pytest.raises(BinanceAuthRequiredError):
                    await client._send_request("test")

    def test_next_id_increments(self) -> None:
        client = BinanceMCPClient()
        assert client._next_id() == 1
        assert client._next_id() == 2
        assert client._next_id() == 3
