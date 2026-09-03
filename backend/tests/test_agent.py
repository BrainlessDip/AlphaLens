from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_chat_request_validation(client: AsyncClient) -> None:
    response = await client.post("/api/v1/agent/chat", json={})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_chat_empty_message_rejected(client: AsyncClient) -> None:
    response = await client.post("/api/v1/agent/chat", json={"message": ""})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_analyze_request_validation(client: AsyncClient) -> None:
    response = await client.post("/api/v1/agent/analyze", json={})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_analyze_missing_symbol(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/agent/analyze",
        json={"question": "Why did it move?"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_chat_streaming_response(client: AsyncClient, mock_provider: MagicMock) -> None:
    from app.api.routes.agent import get_provider
    from app.db.database import get_session as real_get_session

    mock_session = MagicMock()
    mock_session.add.return_value = None
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()

    @asynccontextmanager
    async def fake_run_stream(message, deps=None):
        class FakeStream:
            async def stream_text(self, delta=True):
                yield "Test"
                yield " response"
        yield FakeStream()

    async def override_get_provider():
        return mock_provider

    app.dependency_overrides[get_provider] = override_get_provider

    with patch("app.api.routes.agent.market_agent") as mock_agent:
        mock_agent.run_stream = fake_run_stream
        response = await client.post(
            "/api/v1/agent/chat",
            json={"message": "What is the BTC price?"},
        )
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_analyze_endpoint(client: AsyncClient, mock_provider: MagicMock) -> None:
    from app.api.routes.agent import get_provider

    async def fake_run(prompt, deps=None):
        result = AsyncMock()
        result.output = "BTC shows moderate upward momentum with increasing volume."
        return result

    async def override_get_provider():
        return mock_provider

    app.dependency_overrides[get_provider] = override_get_provider

    with patch("app.api.routes.agent.market_agent") as mock_agent:
        mock_agent.run = fake_run
        response = await client.post(
            "/api/v1/agent/analyze",
            json={"symbol": "BTCUSDT", "question": "Why has BTC moved?"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "BTCUSDT"
        assert data["current_price"] == 60000.0
        assert "agent_analysis" in data
        assert "market_observations" in data
        assert "confidence_and_limitations" in data

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_binance_provider_error_handling() -> None:
    from app.binance.client import BinanceRESTProvider
    provider = AsyncMock(spec=BinanceRESTProvider)
    provider.get_ticker_price.side_effect = Exception("Connection refused")
    with pytest.raises(Exception, match="Connection refused"):
        await provider.get_ticker_price("BTCUSDT")
