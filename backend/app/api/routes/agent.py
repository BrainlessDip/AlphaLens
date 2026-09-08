import asyncio
import json
import logging
import re
import time
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic_ai import Agent
from pydantic_ai.exceptions import ModelHTTPError, UserError
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, TextPart, UserPromptPart
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.agent.agent import get_market_agent, log_run_summary, summarize_run
from app.agent.dependencies import AgentDeps
from app.agent.tools import tool_label
from app.auth.user_auth import current_user_dep
from app.binance.client import BinanceRESTProvider
from app.binance.sub_account_service import get_sub_account_service, is_sub_account_configured
from app.core.config import get_settings
from app.core.exceptions import AgentError, BinanceAPIError
from app.db.database import get_session
from app.db.models import Conversation, Message, User
from app.schemas.agent import AnalyzeRequest, AnalyzeResponse, ChatRequest, PriceInfo, VolumeInfo

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/agent")

HISTORY_LIMIT = 20

_provider: BinanceRESTProvider | None = None


async def get_provider() -> BinanceRESTProvider:
    global _provider
    if _provider is None:
        _provider = BinanceRESTProvider()
    return _provider


def _get_sub_account():
    """Lazy sub-account service init; returns None if not configured."""
    try:
        if is_sub_account_configured():
            return get_sub_account_service()
    except Exception:
        pass
    return None


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


def _title_for(message: str) -> str:
    words = message.strip().split()
    title = " ".join(words[:6])
    return title[:48] if title else "New chat"


# Coins we auto-detect for market data cards. Words outside this set (e.g.
# "AND", "TREND") never become symbols.
KNOWN_BASES = {
    "BTC", "ETH", "BNB", "SOL", "XRP", "ADA", "DOGE", "DOT", "AVAX", "MATIC",
    "LINK", "LTC", "SHIB", "UNI", "ATOM", "XLM", "NEAR", "FIL", "APT", "ARB",
    "OP", "SUI", "TON", "TRX", "PEPE", "INJ", "SEI", "AAVE", "MKR", "RUNE",
}

MAX_MARKET_DATA_SYMBOLS = 4


def _extract_symbols(message: str) -> list[str]:
    """Return up to MAX_MARKET_DATA_SYMBOLS distinct known coin bases from a message."""
    seen: list[str] = []
    for word in re.findall(r"\b[A-Z]{2,10}\b", message.upper()):
        base = word[:-4] if word.endswith("USDT") else word
        if base in KNOWN_BASES and base not in seen:
            seen.append(base)
    return seen[:MAX_MARKET_DATA_SYMBOLS]


def _tool_args_dict(args) -> dict:
    if isinstance(args, dict):
        return args
    if isinstance(args, str):
        try:
            parsed = json.loads(args)
            return parsed if isinstance(parsed, dict) else {}
        except (ValueError, TypeError):
            return {}
    return {}


async def _build_history(session: AsyncSession, conversation_id: str) -> list[ModelMessage]:
    rows = (
        await session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .limit(HISTORY_LIMIT)
        )
    ).scalars().all()
    history: list[ModelMessage] = []
    for m in rows:
        if not m.content:
            continue
        if m.role == "user":
            history.append(ModelRequest(parts=[UserPromptPart(content=m.content)]))
        elif m.role == "assistant":
            history.append(ModelResponse(parts=[TextPart(content=m.content)]))
    return history


def _touch(conversation: Conversation) -> None:
    conversation.updated_at = datetime.now(timezone.utc)


@router.post("/chat", summary="Chat with market agent (SSE stream)")
async def chat(
    request: ChatRequest,
    user: User = Depends(current_user_dep),
    provider: BinanceRESTProvider = Depends(get_provider),
    session: AsyncSession = Depends(get_session),
) -> EventSourceResponse:
    if request.chat_id:
        result = await session.execute(
            select(Conversation).where(
                Conversation.id == request.chat_id,
                Conversation.user_id == user.id,
            )
        )
        conversation = result.scalar_one_or_none()
        if conversation is None:
            raise HTTPException(
                status_code=404,
                detail={"error": {"code": "CHAT_NOT_FOUND", "message": "Chat not found."}},
            )
    else:
        conversation = Conversation(user_id=user.id)
        session.add(conversation)
        await session.commit()
        await session.refresh(conversation)

    history = await _build_history(session, conversation.id)
    if conversation.title == "New chat":
        conversation.title = _title_for(request.message)

    session.add(Message(conversation_id=conversation.id, role="user", content=request.message))
    _touch(conversation)
    await session.commit()

    deps = AgentDeps(provider=provider, sub_account=_get_sub_account())
    model_name = _model_name()
    chat_id = conversation.id

    async def event_generator():
        chunks: list[str] = []
        tool_timings: dict[str, float] = {}
        tools_used: list[dict] = []
        start = time.monotonic()
        yield {"event": "message_start", "data": json.dumps({"type": "message_start", "chat_id": chat_id})}
        try:
            async with get_market_agent().iter(
                request.message, deps=deps, message_history=history or None
            ) as agent_run:
                async for node in agent_run:
                    if Agent.is_model_request_node(node):
                        async with node.stream(agent_run.ctx) as request_stream:
                            async for event in request_stream:
                                kind = getattr(event, "event_kind", None)
                                if kind == "part_delta":
                                    delta = getattr(event, "delta", None)
                                    text = getattr(delta, "content_delta", None)
                                    if isinstance(text, str) and text:
                                        chunks.append(text)
                                        yield {
                                            "event": "assistant_delta",
                                            "data": json.dumps({"type": "assistant_delta", "content": text}),
                                        }
                    elif Agent.is_call_tools_node(node):
                        # Tool events (function_tool_call / function_tool_result) are emitted by
                        # CallToolsNode, not ModelRequestNode. Streaming it also drives tool
                        # execution under `agent.iter()`.
                        async with node.stream(agent_run.ctx) as tool_stream:
                            async for event in tool_stream:
                                kind = getattr(event, "event_kind", None)
                                if kind == "function_tool_call":
                                    part = event.part
                                    tool_name = getattr(part, "tool_name", "unknown")
                                    call_id = getattr(part, "tool_call_id", tool_name)
                                    tool_timings[call_id] = time.monotonic()
                                    label = tool_label(tool_name, _tool_args_dict(getattr(part, "args", None)))
                                    entry = {"tool": tool_name, "label": label}
                                    if entry not in tools_used:
                                        tools_used.append(entry)
                                    yield {
                                        "event": "tool_start",
                                        "data": json.dumps({"type": "tool_start", "tool": tool_name, "label": label}),
                                    }
                                elif kind == "function_tool_result":
                                    part = event.part
                                    tool_name = getattr(part, "tool_name", "unknown")
                                    started = tool_timings.pop(getattr(part, "tool_call_id", tool_name), start)
                                    logger.info(
                                        "agent tool route=chat tool=%s duration_s=%.2f",
                                        tool_name, round(time.monotonic() - started, 2),
                                    )
                                    yield {
                                        "event": "tool_complete",
                                        "data": json.dumps({"type": "tool_complete", "tool": tool_name}),
                                    }
                    # EndNode is iterated but has nothing to stream.
            try:
                result = agent_run.result
                log_run_summary(summarize_run(result, time.monotonic() - start, model_name), "chat")
            except Exception:
                pass
        except (asyncio.CancelledError, GeneratorExit):
            logger.debug("Chat stream cancelled by client")
            complete_text = "".join(chunks)
            if complete_text:
                session.add(Message(conversation_id=chat_id, role="assistant", content=complete_text))
                _touch(conversation)
                try:
                    await session.commit()
                except Exception:
                    pass
            return
        except Exception as e:
            err = map_provider_error(e)
            logger.error("Agent stream error: %s: %s", type(e).__name__, err.message)
            yield {"event": "error", "data": json.dumps({"type": "error", "message": err.message})}
            return

        complete_text = "".join(chunks)
        assistant_msg = Message(conversation_id=chat_id, role="assistant", content=complete_text)
        session.add(assistant_msg)
        _touch(conversation)
        await session.commit()
        await session.refresh(assistant_msg)

        # Emit one market_data event per detected symbol so the UI can render
        # individual cards or a compare table for multi-symbol questions.
        market_data_events: list[dict] = []
        for base in _extract_symbols(request.message):
            sym = f"{base}USDT"
            try:
                ticker = await provider.get_ticker_price(sym)
                stats = await provider.get_ticker_24h(sym)
                market_data_events.append({
                    "type": "market_data",
                    "symbol": ticker.symbol,
                    "price": ticker.price,
                    "change_pct": stats.price_change_percent,
                    "volume_24h": stats.volume,
                    "quote_volume_24h": stats.quote_volume,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
            except Exception:
                continue  # A missing pair must not fail the whole response.

        for event in market_data_events:
            yield {
                "event": "market_data",
                "data": json.dumps(event),
            }

        suggestions = []
        if market_data_events:
            if len(market_data_events) >= 2:
                suggestions = [
                    "Compare their 4h trends",
                    "Which one has stronger momentum?",
                    "What could invalidate this view?",
                ]
            else:
                base_sym = market_data_events[0]["symbol"].replace("USDT", "")
                suggestions = [
                    f"Compare with ETH",
                    f"Show the 4h trend for {base_sym}",
                    f"What could invalidate this view?",
                ]

        yield {
            "event": "message_complete",
            "data": json.dumps({
                "type": "message_complete",
                "chat_id": chat_id,
                "message_id": assistant_msg.id,
                "data_timestamp": datetime.now(timezone.utc).isoformat(),
                "suggestions": suggestions if suggestions else None,
                "tools_used": tools_used,
            }),
        }

    return EventSourceResponse(event_generator())


@router.post("/analyze", response_model=AnalyzeResponse, summary="Structured market analysis")
async def analyze(
    request: AnalyzeRequest,
    user: User = Depends(current_user_dep),
    provider: BinanceRESTProvider = Depends(get_provider),
) -> AnalyzeResponse:
    symbol = request.symbol.upper()

    try:
        ticker = await provider.get_ticker_price(symbol)
        stats = await provider.get_ticker_24h(symbol)
    except Exception as e:
        logger.error("Binance API error for %s: %s", symbol, e)
        raise BinanceAPIError(f"Failed to fetch data for {symbol}: {e}")

    deps = AgentDeps(provider=provider, sub_account=_get_sub_account())
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
