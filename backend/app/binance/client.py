import logging
from typing import Protocol

import httpx

from app.binance.models import Kline, OrderBook, OrderBookEntry, Ticker24h, TickerPrice

logger = logging.getLogger(__name__)

BINANCE_BASE_URL = "https://api.binance.com"


class MarketDataProvider(Protocol):
    async def get_ticker_price(self, symbol: str) -> TickerPrice: ...
    async def get_ticker_24h(self, symbol: str) -> Ticker24h: ...
    async def get_klines(self, symbol: str, interval: str, limit: int) -> list[Kline]: ...
    async def get_order_book(self, symbol: str, limit: int) -> OrderBook: ...


class BinanceRESTProvider:
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(
            base_url=BINANCE_BASE_URL,
            timeout=10.0,
            headers={"Accept": "application/json"},
        )

    async def get_ticker_price(self, symbol: str) -> TickerPrice:
        resp = await self._client.get("/api/v3/ticker/price", params={"symbol": symbol})
        resp.raise_for_status()
        data = resp.json()
        return TickerPrice(symbol=data["symbol"], price=float(data["price"]))

    async def get_ticker_24h(self, symbol: str) -> Ticker24h:
        resp = await self._client.get("/api/v3/ticker/24hr", params={"symbol": symbol})
        resp.raise_for_status()
        data = resp.json()
        return Ticker24h(
            symbol=data["symbol"],
            price_change=float(data["priceChange"]),
            price_change_percent=float(data["priceChangePercent"]),
            weighted_avg_price=float(data["weightedAvgPrice"]),
            prev_close_price=float(data["prevClosePrice"]),
            last_price=float(data["lastPrice"]),
            volume=float(data["volume"]),
            quote_volume=float(data["quoteVolume"]),
            high_price=float(data["highPrice"]),
            low_price=float(data["lowPrice"]),
            open_price=float(data["openPrice"]),
            count=int(data["count"]),
        )

    async def get_klines(self, symbol: str, interval: str = "1h", limit: int = 24) -> list[Kline]:
        resp = await self._client.get(
            "/api/v3/klines",
            params={"symbol": symbol, "interval": interval, "limit": limit},
        )
        resp.raise_for_status()
        data = resp.json()
        return [
            Kline(
                open_time=k[0],
                open=float(k[1]),
                high=float(k[2]),
                low=float(k[3]),
                close=float(k[4]),
                volume=float(k[5]),
                close_time=k[6],
                quote_volume=float(k[7]),
                trades=int(k[8]),
            )
            for k in data
        ]

    async def get_order_book(self, symbol: str, limit: int = 10) -> OrderBook:
        resp = await self._client.get(
            "/api/v3/depth",
            params={"symbol": symbol, "limit": limit},
        )
        resp.raise_for_status()
        data = resp.json()
        return OrderBook(
            last_update_id=data["lastUpdateId"],
            bids=[OrderBookEntry(price=float(b[0]), quantity=float(b[1])) for b in data["bids"]],
            asks=[OrderBookEntry(price=float(a[0]), quantity=float(a[1])) for a in data["asks"]],
        )

    async def close(self) -> None:
        await self._client.aclose()
