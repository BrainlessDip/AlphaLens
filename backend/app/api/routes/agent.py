import json
import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.agent.agent import market_agent
from app.agent.tools import AgentDeps
from app.binance.client import BinanceRESTProvider
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

    async def event_generator() -> dict[str, str]:
        full_response = []
        try:
            async with market_agent.run_stream(request.message, deps=deps) as stream:
                async for text in stream.stream_text(delta=True):
                    full_response.append(text)
                    yield {"event": "message", "data": json.dumps({"type": "token", "content": text})}
        except Exception as e:
            logger.error("Agent stream error: %s", e)
            yield {"event": "error", "data": json.dumps({"type": "error", "message": str(e)})}
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

    try:
        result = await market_agent.run(prompt, deps=deps)
        analysis = result.output
    except Exception as e:
        logger.error("Agent error for %s: %s", symbol, e)
        raise AgentError(f"Analysis failed: {e}")

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
    )
