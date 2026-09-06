from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient

from app.main import app


def _tool_call_event(tool_name: str = "get_ticker", args: str = '{"symbol": "BTCUSDT"}'):
    return SimpleNamespace(
        event_kind="function_tool_call",
        part=SimpleNamespace(tool_name=tool_name, args=args),
    )


def _tool_result_event(tool_name: str = "get_ticker"):
    return SimpleNamespace(
        event_kind="function_tool_result",
        part=SimpleNamespace(tool_name=tool_name),
    )


def _text_delta_event(text: str):
    return SimpleNamespace(
        event_kind="part_delta",
        delta=SimpleNamespace(content_delta=text),
    )


@asynccontextmanager
async def _fake_agent_run_stream(message, deps=None, message_history=None):
    """Fake iter() mirroring the real node flow: ModelRequestNode -> CallToolsNode -> ModelRequestNode -> End."""

    class FakeModelStream:
        def __init__(self, texts):
            self._texts = texts

        async def __aiter__(self):
            for text in self._texts:
                yield _text_delta_event(text)

    class FakeModelNode:
        def __init__(self, texts):
            self._texts = texts

        @asynccontextmanager
        async def stream(self, ctx):
            yield FakeModelStream(self._texts)

    class FakeToolsStream:
        async def __aiter__(self):
            yield _tool_call_event()
            yield _tool_result_event()

    class FakeToolsNode:
        @asynccontextmanager
        async def stream(self, ctx):
            yield FakeToolsStream()

    class FakeEndNode:
        pass

    class FakeAgentRun:
        def __init__(self):
            self._nodes = [
                FakeModelNode(["Test"]),
                FakeToolsNode(),
                FakeModelNode([" response"]),
                FakeEndNode(),
            ]
            self._idx = 0
            self.ctx = SimpleNamespace(deps=SimpleNamespace(new_message_index=0))
            self._result = SimpleNamespace(
                all_messages=lambda: [],
                usage=lambda: SimpleNamespace(requests=1, tool_calls=1, input_tokens=10, output_tokens=20),
            )

        def __aiter__(self):
            return self

        async def __anext__(self):
            if self._idx >= len(self._nodes):
                raise StopAsyncIteration
            node = self._nodes[self._idx]
            self._idx += 1
            return node

    yield FakeAgentRun()


@pytest.fixture
def mock_agent_node_guards():
    """Patch Agent node-type guards to recognize the fake node classes."""
    from pydantic_ai import Agent

    original_is_model_request_node = Agent.is_model_request_node
    original_is_call_tools_node = Agent.is_call_tools_node

    @staticmethod
    def fake_is_model_request_node(node):
        return node.__class__.__name__ == "FakeModelNode"

    @staticmethod
    def fake_is_call_tools_node(node):
        return node.__class__.__name__ == "FakeToolsNode"

    Agent.is_model_request_node = fake_is_model_request_node
    Agent.is_call_tools_node = fake_is_call_tools_node
    yield
    Agent.is_model_request_node = original_is_model_request_node
    Agent.is_call_tools_node = original_is_call_tools_node


@pytest.mark.asyncio
async def test_chat_request_validation(client: AsyncClient, auth_headers: dict) -> None:
    response = await client.post("/api/v1/agent/chat", json={}, headers=auth_headers)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_chat_empty_message_rejected(client: AsyncClient, auth_headers: dict) -> None:
    response = await client.post("/api/v1/agent/chat", json={"message": ""}, headers=auth_headers)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_chat_requires_auth(client: AsyncClient) -> None:
    response = await client.post("/api/v1/agent/chat", json={"message": "Hi"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_analyze_requires_auth(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/agent/analyze", json={"symbol": "BTCUSDT", "question": "Why?"}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_analyze_request_validation(
    client: AsyncClient, auth_headers: dict
) -> None:
    response = await client.post("/api/v1/agent/analyze", json={}, headers=auth_headers)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_analyze_missing_symbol(client: AsyncClient, auth_headers: dict) -> None:
    response = await client.post(
        "/api/v1/agent/analyze",
        json={"question": "Why did it move?"},
        headers=auth_headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_chat_streaming_new_protocol(
    client: AsyncClient, mock_provider: MagicMock, auth_headers: dict, mock_agent_node_guards
) -> None:
    from app.api.routes.agent import get_provider

    async def override_get_provider():
        return mock_provider

    app.dependency_overrides[get_provider] = override_get_provider

    with patch("app.api.routes.agent.get_market_agent") as mock_get_agent:
        mock_get_agent.return_value.iter = _fake_agent_run_stream
        response = await client.post(
            "/api/v1/agent/chat",
            json={"message": "What is the BTC price?"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        body = response.text
        assert '"type": "message_start"' in body
        assert '"type": "tool_start"' in body
        assert '"tool": "get_ticker"' in body
        assert '"type": "assistant_delta"' in body
        assert '"type": "tool_complete"' in body
        assert '"type": "message_complete"' in body
        assert '"type": "token"' not in body  # old protocol gone

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_chat_continues_existing_conversation(
    client: AsyncClient, mock_provider: MagicMock, auth_headers: dict, mock_agent_node_guards
) -> None:
    from app.api.routes.agent import get_provider

    async def override_get_provider():
        return mock_provider

    app.dependency_overrides[get_provider] = override_get_provider

    with patch("app.api.routes.agent.get_market_agent") as mock_get_agent:
        run_stream_spy = MagicMock(side_effect=lambda *a, **k: _fake_agent_run_stream(*a, **k))
        mock_get_agent.return_value.iter = run_stream_spy
        first = await client.post(
            "/api/v1/agent/chat", json={"message": "Hello"}, headers=auth_headers
        )
        assert first.status_code == 200

        chats = await client.get("/api/v1/chats", headers=auth_headers)
        chat_id = chats.json()["items"][0]["id"]

        second = await client.post(
            "/api/v1/agent/chat",
            json={"message": "Follow-up", "chat_id": chat_id},
            headers=auth_headers,
        )
        assert second.status_code == 200

        # history passed to the agent on the second turn
        _, kwargs = run_stream_spy.call_args_list[1]
        history = kwargs.get("message_history")
        assert history is not None and len(history) >= 2

        chats_after = await client.get("/api/v1/chats", headers=auth_headers)
        assert chats_after.json()["total"] == 1

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_chat_unknown_chat_id_404(
    client: AsyncClient, mock_provider: MagicMock, auth_headers: dict
) -> None:
    response = await client.post(
        "/api/v1/agent/chat",
        json={"message": "Hi", "chat_id": "does-not-exist"},
        headers=auth_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_analyze_endpoint(
    client: AsyncClient, mock_provider: MagicMock, auth_headers: dict
) -> None:
    from app.api.routes.agent import get_provider

    async def fake_run(prompt, deps=None):
        result = AsyncMock()
        result.output = "BTC shows moderate upward momentum with increasing volume."
        return result

    async def override_get_provider():
        return mock_provider

    app.dependency_overrides[get_provider] = override_get_provider

    with patch("app.api.routes.agent.get_market_agent") as mock_get_agent:
        mock_get_agent.return_value.run = fake_run
        response = await client.post(
            "/api/v1/agent/analyze",
            json={"symbol": "BTCUSDT", "question": "Why has BTC moved?"},
            headers=auth_headers,
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
