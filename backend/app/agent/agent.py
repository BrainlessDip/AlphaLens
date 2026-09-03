import logging

from pydantic_ai import Agent

from app.agent.prompts import SYSTEM_PROMPT
from app.agent.tools import AgentDeps, get_24h_stats, get_klines, get_order_book, get_ticker

logger = logging.getLogger(__name__)

market_agent = Agent(
    model="openai:gpt-4o",
    system_prompt=SYSTEM_PROMPT,
    deps_type=AgentDeps,
    retries=2,
    tools=[get_ticker, get_24h_stats, get_klines, get_order_book],
    defer_model_check=True,
)
