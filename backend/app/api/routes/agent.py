import asyncio
import json
import logging
import time
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic_ai.exceptions import ModelHTTPError, UserError
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.agent.agent import get_market_agent, log_run_summary, summarize_run
from app.agent.dependencies import AgentDeps
from app.binance.client import BinanceRESTProvider
from app.core.config import get_settings
from app.core.exceptions import AgentError, BinanceAPIError
from app.db.database import get_session
from app.db.models import Conversation, Message
from app.schemas.agent import AnalyzeRequest, AnalyzeResponse, ChatRequest, PriceInfo, VolumeInfo

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/agent")

_provider: BinanceRESTProvider | None = None


async def get_provider() -> BinanceRESTProvider:
    global _provider
    if _provider is None:
        _provider = BinanceRESTProvider()
    return _provider


def map_provider_error(e: Exception) -> AgentError:
    """Map LLM provider failures to clean API errors (never leak keys or internals)."""
    if isinstance(e, UserError):
        return AgentError("LLM provider is not configured. Set OPENROUTER_API_KEY on the server.")
    if isinstance(e, ModelHTTPError):
        if e.status_code == 401:
            return AgentError("LLM provider authentication failed. Check server configuration.")
        if e.status_code == 429:
            return AgentError("LLM provider rate limit reached. Please try again shortly.")
        if e.status_code == 404:
            return AgentError("Configured LLM model is unavailable.")
        return AgentError(f"LLM provider error (HTTP {e.status_code}). Please try again later.")
    if isinstance(e, (asyncio.TimeoutError, TimeoutError)):
        return AgentError("LLM request timed out. Please try again.")
    return AgentError("Analysis failed. Please try again later.")


def _model_name() -> str:
    return get_settings().openrouter_model


@router.post("/chat", summary="Chat with market agent (SSE stream)")
async def chat(
    request: ChatRequest,
    provider: BinanceRESTProvider = Depends(get_provider),
    session: AsyncSession = Depends(get_session),
) -> EventSourceResponse:
    conversation = Conversation()
    session.add(conversation)
    await session.commit()
    await session.refresh(conversation)

    session.add(Message(conversation_id=conversation.id, role="user", content=request.message))
    await session.commit()

    deps = AgentDeps(provider=provider)
    model_name = _model_name()

    async def event_generator() -> dict[str, str]:
        full_response = []
        start = time.monotonic()
        try:
            async with get_market_agent().run_stream(request.message, deps=deps) as stream:
                async for text in stream.stream_text(delta=True):
                    full_response.append(text)
                    yield {"event": "message", "data": json.dumps({"type": "token", "content": text})}
            try:
                log_run_summary(summarize_run(stream, time.monotonic() - start, model_name), "chat")
            except Exception:
                pass
        except (asyncio.CancelledError, GeneratorExit):
            logger.info("Chat stream cancelled by client")
            return
        except Exception as e:
            err = map_provider_error(e)
            logger.error("Agent stream error: %s: %s", type(e).__name__, err.message)
            yield {"event": "error", "data": json.dumps({"type": "error", "message": err.message})}
            return

        complete_text = "".join(full_response)
        session.add(Message(conversation_id=conversation.id, role="assistant", content=complete_text))
        await session.commit()

        yield {"event": "message", "data": json.dumps({"type": "done", "conversation_id": conversation.id})}

    return EventSourceResponse(event_generator())


@router.post("/analyze", response_model=AnalyzeResponse, summary="Structured market analysis")
async def analyze(
    request: AnalyzeRequest,
    provider: BinanceRESTProvider = Depends(get_provider),
) -> AnalyzeResponse:
    symbol = request.symbol.upper()

    try:
        ticker = await provider.get_ticker_price(symbol)
        stats = await provider.get_ticker_24h(symbol)
    except Exception as e:
        logger.error("Binance API error for %s: %s", symbol, e)
        raise BinanceAPIError(f"Failed to fetch data for {symbol}: {e}")

    deps = AgentDeps(provider=provider)
    prompt = f"Analyze {symbol} market conditions. {request.question}"

    start = time.monotonic()
    try:
        result = await get_market_agent().run(prompt, deps=deps)
        analysis = result.output
        try:
            log_run_summary(summarize_run(result, time.monotonic() - start, _model_name()), "analyze")
        except Exception:
            pass
    except Exception as e:
        err = map_provider_error(e)
        logger.error("Agent error for %s: %s: %s", symbol, type(e).__name__, err.message)
        raise err

    observations = []
    if stats.price_change_percent > 5:
        observations.append(f"Significant 24h price increase of {stats.price_change_percent:+.2f}%")
    elif stats.price_change_percent < -5:
        observations.append(f"Significant 24h price decrease of {stats.price_change_percent:+.2f}%")
    else:
        observations.append(f"Moderate 24h price movement of {stats.price_change_percent:+.2f}%")

    if stats.volume > 1_000_000:
        observations.append(f"High trading volume: {stats.volume:,.0f} units")
    else:
        observations.append(f"Trading volume: {stats.volume:,.0f} units")

    observations.append(f"24h range: ${stats.low_price:,.2f} - ${stats.high_price:,.2f}")

    return AnalyzeResponse(
        symbol=symbol,
        current_price=ticker.price,
        price_change=PriceInfo(
            symbol=symbol,
            price=ticker.price,
            change_pct=stats.price_change_percent,
        ),
        volume_info=VolumeInfo(
            volume_24h=stats.volume,
            quote_volume_24h=stats.quote_volume,
        ),
        market_observations=observations,
        agent_analysis=analysis,
        confidence_and_limitations=(
            "This analysis is based on publicly available Binance market data only. "
            "It does not account for off-chain factors, news events, regulatory changes, "
            "or whale movements. This is observational analysis, not financial advice."
        ),
        data_timestamp=datetime.now(timezone.utc).isoformat(),
    )
