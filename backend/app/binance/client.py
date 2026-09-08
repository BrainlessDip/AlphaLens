import asyncio
import logging
from typing import Protocol

import httpx

from app.binance.models import (
    ExchangeInfo,
    Kline,
    OrderBook,
    OrderBookEntry,
    RecentTrade,
    Ticker24h,
    TickerPrice,
)
from app.core.config import get_settings
from app.core.exceptions import BinanceAPIError

logger = logging.getLogger(__name__)


def _validate_symbol(symbol: str) -> str:
    cleaned = symbol.strip().upper()
    if not cleaned or len(cleaned) > 20 or not cleaned.isalnum():
        raise BinanceAPIError(f"Invalid symbol: {symbol!r}")
    return cleaned


class MarketDataProvider(Protocol):
    async def get_ticker_price(self, symbol: str) -> TickerPrice: ...
    async def get_ticker_24h(self, symbol: str) -> Ticker24h: ...
    async def get_klines(self, symbol: str, interval: str, limit: int) -> list[Kline]: ...
    async def get_order_book(self, symbol: str, limit: int) -> OrderBook: ...
    async def get_recent_trades(self, symbol: str, limit: int) -> list[RecentTrade]: ...
    async def get_exchange_info(self) -> ExchangeInfo: ...


class BinanceRESTProvider:
    """Direct Binance Spot REST API client (public market data, no auth required)."""

    def __init__(self) -> None:
        settings = get_settings()
        self._client = httpx.AsyncClient(
            base_url=settings.binance_effective_base_url,
            timeout=settings.binance_request_timeout,
            headers={"Accept": "application/json"},
        )

    async def _get(self, path: str, params: dict | None = None) -> httpx.Response:
        try:
            resp = await self._client.get(path, params=params)
        except httpx.TimeoutException as e:
            raise BinanceAPIError(f"Binance API timeout for {path}") from e
        except httpx.RequestError as e:
            raise BinanceAPIError(f"Binance API unavailable: {type(e).__name__}") from e

        if resp.status_code in (429, 418):
            retry_after = resp.headers.get("Retry-After", "unknown")
            raise BinanceAPIError(
                f"Binance rate limit hit (retry after {retry_after}s). Please try again shortly."
            )
        if resp.status_code == 400:
            # Binance returns {"code": -1121, "msg": "Invalid symbol."} etc. Safe to surface msg.
            try:
                msg = resp.json().get("msg", "Bad request")
            except Exception:
                msg = "Bad request"
            raise BinanceAPIError(f"Binance rejected request: {msg}")
        if resp.status_code != 200:
            raise BinanceAPIError(f"Binance API error: HTTP {resp.status_code} for {path}")
        return resp

    async def get_ticker_price(self, symbol: str) -> TickerPrice:
        symbol = _validate_symbol(symbol)
        resp = await self._get("/api/v3/ticker/price", params={"symbol": symbol})
        data = resp.json()
        try:
            return TickerPrice(symbol=data["symbol"], price=float(data["price"]))
        except (KeyError, TypeError, ValueError) as e:
            raise BinanceAPIError(f"Malformed ticker response for {symbol}") from e

    async def get_ticker_24h(self, symbol: str) -> Ticker24h:
        symbol = _validate_symbol(symbol)
        resp = await self._get("/api/v3/ticker/24hr", params={"symbol": symbol})
        data = resp.json()
        try:
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
        except (KeyError, TypeError, ValueError) as e:
            raise BinanceAPIError(f"Malformed 24h ticker response for {symbol}") from e

    async def get_klines(self, symbol: str, interval: str = "1h", limit: int = 24) -> list[Kline]:
        symbol = _validate_symbol(symbol)
        if interval not in {"1m", "5m", "15m", "1h", "4h", "1d"}:
            raise BinanceAPIError(f"Unsupported interval: {interval!r}")
        limit = max(1, min(limit, 200))
        resp = await self._get(
            "/api/v3/klines",
            params={"symbol": symbol, "interval": interval, "limit": limit},
        )
        try:
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
                for k in resp.json()
            ]
        except (TypeError, ValueError, IndexError) as e:
            raise BinanceAPIError(f"Malformed kline response for {symbol}") from e

    async def get_order_book(self, symbol: str, limit: int = 10) -> OrderBook:
        symbol = _validate_symbol(symbol)
        limit = max(1, min(limit, 100))
        resp = await self._get(
            "/api/v3/depth",
            params={"symbol": symbol, "limit": limit},
        )
        data = resp.json()
        try:
            return OrderBook(
                last_update_id=data["lastUpdateId"],
                bids=[OrderBookEntry(price=float(b[0]), quantity=float(b[1])) for b in data["bids"]],
                asks=[OrderBookEntry(price=float(a[0]), quantity=float(a[1])) for a in data["asks"]],
            )
        except (KeyError, TypeError, ValueError) as e:
            raise BinanceAPIError(f"Malformed order book response for {symbol}") from e

    async def get_recent_trades(self, symbol: str, limit: int = 20) -> list[RecentTrade]:
        symbol = _validate_symbol(symbol)
        limit = max(1, min(limit, 100))
        resp = await self._get(
            "/api/v3/trades",
            params={"symbol": symbol, "limit": limit},
        )
        try:
            return [
                RecentTrade(
                    id=t["id"],
                    price=float(t["price"]),
                    quantity=float(t["qty"]),
                    time=t["time"],
                    is_buyer_maker=bool(t["isBuyerMaker"]),
                )
                for t in resp.json()
            ]
        except (KeyError, TypeError, ValueError) as e:
            raise BinanceAPIError(f"Malformed trades response for {symbol}") from e

    async def get_exchange_info(self) -> ExchangeInfo:
        resp = await self._get("/api/v3/exchangeInfo")
        data = resp.json()
        try:
            symbols = [s["symbol"] for s in data.get("symbols", []) if s.get("status") == "TRADING"]
            return ExchangeInfo(timezone=data.get("timezone", "UTC"), trading_symbols=symbols)
        except (TypeError, ValueError) as e:
            raise BinanceAPIError("Malformed exchange info response") from e

    async def get_market_snapshot(
        self, symbol: str, klines_interval: str = "1h", klines_limit: int = 24
    ) -> dict:
        """Fetch price + 24h stats + klines concurrently (independent requests)."""
        symbol = _validate_symbol(symbol)
        price_coro = self.get_ticker_price(symbol)
        stats_coro = self.get_ticker_24h(symbol)
        klines_coro = self.get_klines(symbol, klines_interval, klines_limit)
        ticker, stats, klines = await asyncio.gather(price_coro, stats_coro, klines_coro)
        return {"ticker": ticker, "stats_24h": stats, "klines": klines}

    async def close(self) -> None:
        await self._client.aclose()
