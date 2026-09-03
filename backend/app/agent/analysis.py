"""Deterministic market calculations over Binance data.

The LLM must never compute indicators over large datasets by hand;
these helpers do it reliably in Python.
"""

from app.binance.models import Kline


def closes(klines: list[Kline]) -> list[float]:
    return [k.close for k in klines]


def simple_moving_average(values: list[float], period: int) -> float | None:
    if len(values) < period or period <= 0:
        return None
    return sum(values[-period:]) / period


def exponential_moving_average(values: list[float], period: int) -> float | None:
    if len(values) < period or period <= 0:
        return None
    k = 2 / (period + 1)
    ema = values[-period]
    for v in values[-period + 1 :]:
        ema = v * k + ema * (1 - k)
    return ema


def rsi(values: list[float], period: int = 14) -> float | None:
    """Wilder's RSI over closing prices. Returns None when insufficient data."""
    if len(values) < period + 1 or period <= 0:
        return None
    gains: list[float] = []
    losses: list[float] = []
    for i in range(1, period + 1):
        delta = values[-i] - values[-i - 1]
        gains.append(max(delta, 0.0))
        losses.append(max(-delta, 0.0))
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def volatility_pct(values: list[float], period: int = 24) -> float | None:
    """Standard deviation of simple returns over the last `period` closes, in percent."""
    if len(values) < period + 1 or period <= 0:
        return None
    window = values[-(period + 1) :]
    returns = [(window[i] - window[i - 1]) / window[i - 1] for i in range(1, len(window)) if window[i - 1] != 0]
    if not returns:
        return None
    mean = sum(returns) / len(returns)
    var = sum((r - mean) ** 2 for r in returns) / len(returns)
    return (var**0.5) * 100


def support_resistance(klines: list[Kline]) -> dict[str, float | None]:
    """Naive swing levels from candle wicks over the given window."""
    if not klines:
        return {"support": None, "resistance": None}
    return {
        "support": min(k.low for k in klines),
        "resistance": max(k.high for k in klines),
    }


def volume_summary(klines: list[Kline]) -> dict[str, float | None]:
    """Average vs latest candle volume; None when no data."""
    if not klines:
        return {"average": None, "latest": None, "ratio": None}
    vols = [k.volume for k in klines]
    avg = sum(vols) / len(vols)
    latest = vols[-1]
    return {"average": avg, "latest": latest, "ratio": (latest / avg) if avg else None}
