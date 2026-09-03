import logging

from pydantic_ai import Agent

from app.agent.prompts import SYSTEM_PROMPT
from app.agent.tools import (
    AgentDeps,
    get_24h_stats,
    get_exchange_info,
    get_indicators,
    get_klines,
    get_order_book,
    get_recent_trades,
    get_ticker,
)
from app.core.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

market_agent = Agent(
    model=f"openai:{settings.llm_model}",
    system_prompt=SYSTEM_PROMPT,
    deps_type=AgentDeps,
    retries=2,
    tools=[
        get_ticker,
        get_24h_stats,
        get_klines,
        get_order_book,
        get_recent_trades,
        get_exchange_info,
        get_indicators,
    ],
    defer_model_check=True,
)
