from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from pydantic_ai.exceptions import ModelHTTPError, UserError
from pydantic_ai.models.openrouter import OpenRouterModel

from app.agent.agent import build_market_agent, build_model, summarize_run
from app.api.routes.agent import map_provider_error
from app.core.config import Settings
from app.core.exceptions import AgentError

EXPECTED_TOOLS = {
    "get_ticker",
    "get_24h_stats",
    "get_klines",
    "get_order_book",
    "get_recent_trades",
    "get_exchange_info",
    "get_indicators",
}


def _settings(**overrides) -> Settings:
    return Settings(openrouter_api_key="test-key", **overrides)


class TestOpenRouterWiring:
    def test_model_uses_configured_name(self) -> None:
        agent = build_market_agent(_settings(openrouter_model="openai/gpt-4o-mini"))
        assert isinstance(agent.model, OpenRouterModel)
        assert agent.model.model_name == "openai/gpt-4o-mini"

    def test_default_model(self) -> None:
        assert Settings.model_fields["openrouter_model"].default == "openai/gpt-4o-mini"

    def test_all_binance_tools_registered(self) -> None:
        agent = build_market_agent(_settings())
        names = {t.name for t in agent._function_toolset.tools.values()}
        assert EXPECTED_TOOLS <= names

    def test_no_forced_tool_choice(self) -> None:
        agent = build_market_agent(_settings())
        assert agent.model_settings is None

    def test_provider_receives_attribution(self) -> None:
        model = build_model(_settings(
            openrouter_app_url="https://example.com",
            openrouter_app_title="Test App",
        ))
        assert isinstance(model, OpenRouterModel)

    def test_missing_key_raises_user_error(self) -> None:
        with pytest.raises(UserError):
            build_model(Settings(openrouter_api_key=""))


class TestProviderErrorMapping:
    def test_401_auth_failure(self) -> None:
        err = map_provider_error(ModelHTTPError(401, "openai/gpt-4o-mini"))
        assert isinstance(err, AgentError)
        assert "authentication" in err.message

    def test_429_rate_limit(self) -> None:
        err = map_provider_error(ModelHTTPError(429, "openai/gpt-4o-mini"))
        assert "rate limit" in err.message

    def test_404_model_unavailable(self) -> None:
        err = map_provider_error(ModelHTTPError(404, "nope/model"))
        assert "unavailable" in err.message

    def test_500_provider_error(self) -> None:
        err = map_provider_error(ModelHTTPError(500, "openai/gpt-4o-mini"))
        assert "HTTP 500" in err.message

    def test_timeout(self) -> None:
        err = map_provider_error(TimeoutError("timed out"))
        assert "timed out" in err.message

    def test_unconfigured_provider(self) -> None:
        err = map_provider_error(UserError("Set the `OPENROUTER_API_KEY` env var"))
        assert "not configured" in err.message
        assert "OPENROUTER_API_KEY" in err.message

    def test_no_secret_leak_in_mapping(self) -> None:
        evil = ModelHTTPError(400, "m", body={"detail": "key sk-or-SECRET-123 rejected"})
        err = map_provider_error(evil)
        assert "sk-or-SECRET-123" not in err.message

    def test_generic_error_is_sanitized(self) -> None:
        err = map_provider_error(RuntimeError("sk-or-SECRET-123 exploded"))
        assert "sk-or-SECRET-123" not in err.message


class TestRunSummary:
    def _fake_result(self):
        part1 = SimpleNamespace(part_kind="tool-call", tool_name="get_ticker")
        part2 = SimpleNamespace(part_kind="tool-call", tool_name="get_24h_stats")
        part3 = SimpleNamespace(part_kind="text", content="done")
        usage = SimpleNamespace(requests=2, tool_calls=2, input_tokens=100, output_tokens=50)
        return SimpleNamespace(
            all_messages=lambda: [SimpleNamespace(parts=[part1, part2, part3])],
            usage=lambda: usage,
        )

    def test_summary_extracts_tools_and_usage(self) -> None:
        s = summarize_run(self._fake_result(), 1.234, "openai/gpt-4o-mini")
        assert s["model"] == "openai/gpt-4o-mini"
        assert s["tools_called"] == ["get_ticker", "get_24h_stats"]
        assert s["num_tool_calls"] == 2
        assert s["usage"]["tool_calls"] == 2
        assert s["duration_s"] == 1.23

    def test_summary_defensive_on_broken_result(self) -> None:
        class Broken:
            def all_messages(self):
                raise RuntimeError("boom")

            def usage(self):
                raise RuntimeError("boom")

        s = summarize_run(Broken(), 0.5, "m")
        assert s["tools_called"] == []
        assert s["usage"] == {}

    def test_summary_never_includes_reasoning(self) -> None:
        s = summarize_run(self._fake_result(), 0.1, "m")
        flat = str(s)
        assert "chain" not in flat.lower()
