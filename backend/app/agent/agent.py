import inspect
import logging
from typing import Any

from pydantic_ai import Agent
from pydantic_ai.models.openrouter import OpenRouterModel
from pydantic_ai.providers.openrouter import OpenRouterProvider

from app.agent.dependencies import AgentDeps
from app.agent.prompts import SYSTEM_PROMPT
from app.agent.tools import (
    get_24h_stats,
    get_exchange_info,
    get_indicators,
    get_klines,
    get_order_book,
    get_recent_trades,
    get_ticker,
    get_sub_accounts,
    get_sub_account_assets,
    get_sub_account_spot_summary,
    get_sub_account_futures_account,
    get_sub_account_futures_positions,
    get_sub_account_futures_summary,
    get_sub_account_margin_account,
    get_sub_account_margin_summary,
    get_sub_account_transfer_history,
    get_sub_account_futures_transfer_history,
    get_sub_account_universal_transfer_history,
    get_sub_account_deposit_history,
)
from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)

_cached_agent: Agent[AgentDeps, str] | None = None


def build_model(settings: Settings) -> OpenRouterModel:
    """Centralized OpenRouter model/provider configuration.

    The API key falls back to the OPENROUTER_API_KEY environment variable
    when not set in settings. Attribution headers fall back to
    OPENROUTER_APP_URL / OPENROUTER_APP_TITLE.
    """
    provider_kwargs: dict[str, Any] = {}
    if settings.openrouter_api_key:
        provider_kwargs["api_key"] = settings.openrouter_api_key
    if settings.openrouter_app_url:
        provider_kwargs["app_url"] = settings.openrouter_app_url
    if settings.openrouter_app_title:
        provider_kwargs["app_title"] = settings.openrouter_app_title
    provider = OpenRouterProvider(**provider_kwargs)
    return OpenRouterModel(settings.openrouter_model, provider=provider)


def build_market_agent(settings: Settings | None = None) -> Agent[AgentDeps, str]:
    """Factory for the market intelligence agent (also used in tests)."""
    settings = settings or get_settings()
    tools = [
        get_ticker,
        get_24h_stats,
        get_klines,
        get_order_book,
        get_recent_trades,
        get_exchange_info,
        get_indicators,
    ]

    # Register sub-account tools only if credentials are configured
    from app.binance.sub_account_service import is_sub_account_configured
    if is_sub_account_configured():
        tools.extend([
            get_sub_accounts,
            get_sub_account_assets,
            get_sub_account_spot_summary,
            get_sub_account_futures_account,
            get_sub_account_futures_positions,
            get_sub_account_futures_summary,
            get_sub_account_margin_account,
            get_sub_account_margin_summary,
            get_sub_account_transfer_history,
            get_sub_account_futures_transfer_history,
            get_sub_account_universal_transfer_history,
            get_sub_account_deposit_history,
        ])

    return Agent(
        build_model(settings),
        system_prompt=SYSTEM_PROMPT,
        deps_type=AgentDeps,
        retries=2,
        tools=tools,
        defer_model_check=True,
    )


def get_market_agent() -> Agent[AgentDeps, str]:
    """Lazily-built shared agent.

    Construction is deferred to request time so importing this module never
    requires an API key. Raises UserError if no OpenRouter key is configured.
    """
    global _cached_agent
    if _cached_agent is None:
        _cached_agent = build_market_agent()
    return _cached_agent


def _close_awaitable(value: Any) -> None:
    close = getattr(value, "close", None)
    if callable(close):
        try:
            close()
        except Exception:
            pass


def summarize_run(result: Any, duration_s: float, model_name: str) -> dict[str, Any]:
    """Extract safe run metadata for logging (no chain-of-thought, no secrets)."""
    tool_names: list[str] = []
    try:
        messages = result.all_messages()
        if inspect.isawaitable(messages):
            _close_awaitable(messages)
            raise TypeError("unexpected awaitable")
        for message in messages:
            for part in getattr(message, "parts", []) or []:
                if getattr(part, "part_kind", None) == "tool-call":
                    name = getattr(part, "tool_name", None)
                    if name:
                        tool_names.append(name)
    except Exception:
        pass

    usage: dict[str, Any] = {}
    try:
        u = result.usage()
        if inspect.isawaitable(u):
            _close_awaitable(u)
            raise TypeError("unexpected awaitable")
        usage = {
            "requests": u.requests,
            "tool_calls": u.tool_calls,
            "input_tokens": u.input_tokens,
            "output_tokens": u.output_tokens,
        }
    except Exception:
        pass

    return {
        "model": model_name,
        "duration_s": round(duration_s, 2),
        "tools_called": tool_names,
        "num_tool_calls": len(tool_names),
        "usage": usage,
    }


def log_run_summary(summary: dict[str, Any], route: str) -> None:
    logger.info("agent run route=%s model=%s duration_s=%s tool_calls=%s tools=%s usage=%s",
                route, summary["model"], summary["duration_s"],
                summary["num_tool_calls"], summary["tools_called"], summary["usage"])
