from typing import AsyncIterator
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.binance.client import BinanceRESTProvider
from app.binance.models import Kline, OrderBook, OrderBookEntry, Ticker24h, TickerPrice
from app.db.database import get_session
from app.db.models import Base
from app.main import app


@pytest.fixture
def mock_provider() -> MagicMock:
    provider = AsyncMock(spec=BinanceRESTProvider)
    provider.get_ticker_price.return_value = TickerPrice(symbol="BTCUSDT", price=60000.0)
    provider.get_ticker_24h.return_value = Ticker24h(
        symbol="BTCUSDT",
        price_change=1500.0,
        price_change_percent=2.5,
        weighted_avg_price=59800.0,
        prev_close_price=58500.0,
        last_price=60000.0,
        volume=12345.67,
        quote_volume=738_940_200.0,
        high_price=60500.0,
        low_price=58000.0,
        open_price=58500.0,
        count=1_234_567,
    )
    provider.get_klines.return_value = [
        Kline(
            open_time=1690000000000,
            open=58500.0,
            high=60000.0,
            low=58000.0,
            close=59500.0,
            volume=1000.0,
            close_time=1690003600000,
            quote_volume=59_500_000.0,
            trades=5000,
        )
    ]
    provider.get_order_book.return_value = OrderBook(
        last_update_id=12345,
        bids=[OrderBookEntry(price=59900.0, quantity=1.5)],
        asks=[OrderBookEntry(price=60100.0, quantity=2.0)],
    )
    return provider


@pytest.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    await engine.dispose()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncIterator[AsyncClient]:
    async def override_get_session():
        yield db_session

    app.dependency_overrides[get_session] = override_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
