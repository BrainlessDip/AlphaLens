from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from app.binance.client import BinanceRESTProvider, _validate_symbol
from app.core.exceptions import BinanceAPIError


def _make_provider(monkeypatch, handler) -> BinanceRESTProvider:
    provider = BinanceRESTProvider.__new__(BinanceRESTProvider)
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=handler)
    provider._client = mock_client
    return provider


def _resp(status: int, payload, headers=None) -> MagicMock:
    r = MagicMock()
    r.status_code = status
    r.json.return_value = payload
    r.headers = headers or {}
    return r


class TestSymbolValidation:
    def test_valid_symbol_uppercased(self) -> None:
        assert _validate_symbol("btcusdt") == "BTCUSDT"

    def test_invalid_symbols_rejected(self) -> None:
        for bad in ["", "BTC/USDT", "BTC USDT", "x" * 21, "BTC-USD!"]:
            with pytest.raises(BinanceAPIError):
                _validate_symbol(bad)


class TestErrorHandling:
    @pytest.mark.asyncio
    async def test_timeout_maps_to_binance_error(self, monkeypatch) -> None:
        async def handler(path, params=None):
            raise httpx.TimeoutException("timed out")

        provider = _make_provider(monkeypatch, handler)
        with pytest.raises(BinanceAPIError, match="timeout"):
            await provider.get_ticker_price("BTCUSDT")

    @pytest.mark.asyncio
    async def test_rate_limit_maps_to_binance_error(self, monkeypatch) -> None:
        async def handler(path, params=None):
            return _resp(429, {"code": -1003, "msg": "Too many requests"}, {"Retry-After": "60"})

        provider = _make_provider(monkeypatch, handler)
        with pytest.raises(BinanceAPIError, match="rate limit"):
            await provider.get_ticker_price("BTCUSDT")

    @pytest.mark.asyncio
    async def test_invalid_symbol_message_surfaced(self, monkeypatch) -> None:
        async def handler(path, params=None):
            return _resp(400, {"code": -1121, "msg": "Invalid symbol."})

        provider = _make_provider(monkeypatch, handler)
        with pytest.raises(BinanceAPIError, match="Invalid symbol"):
            await provider.get_ticker_price("NOPE")

    @pytest.mark.asyncio
    async def test_malformed_response_rejected(self, monkeypatch) -> None:
        async def handler(path, params=None):
            return _resp(200, {"unexpected": "shape"})

        provider = _make_provider(monkeypatch, handler)
        with pytest.raises(BinanceAPIError, match="Malformed"):
            await provider.get_ticker_price("BTCUSDT")

    @pytest.mark.asyncio
    async def test_no_secrets_in_errors(self, monkeypatch) -> None:
        async def handler(path, params=None):
            return _resp(500, "boom")

        provider = _make_provider(monkeypatch, handler)
        try:
            await provider.get_ticker_price("BTCUSDT")
            raise AssertionError("should have raised")
        except BinanceAPIError as e:
            assert "api_key" not in e.message.lower()
            assert "secret" not in e.message.lower()


class TestNewEndpoints:
    @pytest.mark.asyncio
    async def test_get_recent_trades(self, monkeypatch) -> None:
        async def handler(path, params=None):
            assert path == "/api/v3/trades"
            return _resp(200, [
                {"id": 1, "price": "60000.0", "qty": "0.5", "time": 1690000000000, "isBuyerMaker": False},
            ])

        provider = _make_provider(monkeypatch, handler)
        trades = await provider.get_recent_trades("BTCUSDT", limit=5)
        assert len(trades) == 1
        assert trades[0].price == 60000.0
        assert trades[0].is_buyer_maker is False

    @pytest.mark.asyncio
    async def test_get_exchange_info(self, monkeypatch) -> None:
        async def handler(path, params=None):
            assert path == "/api/v3/exchangeInfo"
            return _resp(200, {
                "timezone": "UTC",
                "symbols": [
                    {"symbol": "BTCUSDT", "status": "TRADING"},
                    {"symbol": "OLDCOIN", "status": "BREAK"},
                ],
            })

        provider = _make_provider(monkeypatch, handler)
        info = await provider.get_exchange_info()
        assert info.trading_symbols == ["BTCUSDT"]

    @pytest.mark.asyncio
    async def test_bad_interval_rejected(self, monkeypatch) -> None:
        provider = _make_provider(monkeypatch, AsyncMock())
        with pytest.raises(BinanceAPIError, match="interval"):
            await provider.get_klines("BTCUSDT", interval="3y", limit=10)
