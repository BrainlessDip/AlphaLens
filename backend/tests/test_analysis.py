from app.agent.analysis import (
    exponential_moving_average,
    rsi,
    simple_moving_average,
    support_resistance,
    volatility_pct,
    volume_summary,
)
from app.binance.models import Kline


def _klines(closes: list[float]) -> list[Kline]:
    return [
        Kline(
            open_time=i,
            open=c,
            high=c + 10,
            low=c - 10,
            close=c,
            volume=100.0 + i,
            close_time=i,
            quote_volume=1000.0,
            trades=10,
        )
        for i, c in enumerate(closes)
    ]


class TestMovingAverages:
    def test_sma(self) -> None:
        assert simple_moving_average([1, 2, 3, 4, 5], 3) == 4.0

    def test_sma_insufficient_data(self) -> None:
        assert simple_moving_average([1, 2], 3) is None

    def test_ema_flat_series(self) -> None:
        assert exponential_moving_average([5, 5, 5, 5, 5], 3) == 5.0

    def test_ema_insufficient_data(self) -> None:
        assert exponential_moving_average([1, 2], 5) is None


class TestRSI:
    def test_rsi_all_gains_is_100(self) -> None:
        assert rsi([float(i) for i in range(20)], 14) == 100.0

    def test_rsi_all_losses_is_0(self) -> None:
        assert rsi([float(20 - i) for i in range(20)], 14) == 0.0

    def test_rsi_insufficient_data(self) -> None:
        assert rsi([1.0, 2.0, 3.0], 14) is None


class TestVolatilityAndLevels:
    def test_volatility_flat_is_zero(self) -> None:
        assert volatility_pct([100.0] * 30, 24) == 0.0

    def test_volatility_insufficient_data(self) -> None:
        assert volatility_pct([1.0, 2.0], 24) is None

    def test_support_resistance(self) -> None:
        sr = support_resistance(_klines([100.0, 110.0, 90.0]))
        assert sr["support"] == 80.0
        assert sr["resistance"] == 120.0

    def test_support_resistance_empty(self) -> None:
        sr = support_resistance([])
        assert sr["support"] is None
        assert sr["resistance"] is None

    def test_volume_summary(self) -> None:
        vs = volume_summary(_klines([100.0, 101.0, 102.0]))
        assert vs["latest"] == 102.0
        assert vs["average"] == 101.0
        assert vs["ratio"] is not None
