import logging
from dataclasses import dataclass

from pydantic_ai import RunContext

from app.agent.analysis import (
    closes,
    exponential_moving_average,
    rsi,
    simple_moving_average,
    support_resistance,
    volatility_pct,
    volume_summary,
)
from app.binance.client import BinanceRESTProvider

logger = logging.getLogger(__name__)


@dataclass
class AgentDeps:
    provider: BinanceRESTProvider


async def get_ticker(ctx: RunContext[AgentDeps], symbol: str) -> str:
    """Get current price for a trading pair. Example: BTCUSDT, ETHUSDT"""
    try:
        ticker = await ctx.deps.provider.get_ticker_price(symbol.upper())
        return f"Current {ticker.symbol} price: ${ticker.price:,.2f}"
    except Exception as e:
        logger.error("get_ticker failed for %s: %s", symbol, e)
        return f"Error fetching ticker for {symbol}: {e}"


async def get_24h_stats(ctx: RunContext[AgentDeps], symbol: str) -> str:
    """Get 24-hour rolling window statistics for a trading pair. Includes price change, volume, high/low."""
    try:
        stats = await ctx.deps.provider.get_ticker_24h(symbol.upper())
        return (
            f"24h stats for {stats.symbol}:\n"
            f"  Price: ${stats.last_price:,.2f}\n"
            f"  Change: {stats.price_change_percent:+.2f}% (${stats.price_change:+,.2f})\n"
            f"  High: ${stats.high_price:,.2f} | Low: ${stats.low_price:,.2f}\n"
            f"  Volume: {stats.volume:,.2f} {stats.symbol.replace('USDT', '')}\n"
            f"  Quote Volume: ${stats.quote_volume:,.2f}\n"
            f"  Trades: {stats.count:,}"
        )
    except Exception as e:
        logger.error("get_24h_stats failed for %s: %s", symbol, e)
        return f"Error fetching 24h stats for {symbol}: {e}"


async def get_klines(
    ctx: RunContext[AgentDeps],
    symbol: str,
    interval: str = "1h",
    limit: int = 24,
) -> str:
    """Get candlestick/kline data. Interval options: 1m, 5m, 15m, 1h, 4h, 1d. Limit: number of candles (max 200)."""
    try:
        klines = await ctx.deps.provider.get_klines(symbol.upper(), interval, min(limit, 200))
        if not klines:
            return f"No kline data found for {symbol}"

        lines = [f"Kline data for {symbol.upper()} ({interval}, last {len(klines)} candles):"]
        for k in klines[-10:]:  # Show last 10 for readability
            lines.append(
                f"  {k.open_time} | O: ${k.open:,.2f} H: ${k.high:,.2f} L: ${k.low:,.2f} C: ${k.close:,.2f} V: {k.volume:,.2f}"
            )

        first_close = klines[0].close
        last_close = klines[-1].close
        change_pct = ((last_close - first_close) / first_close) * 100
        lines.append(f"\nPeriod change: {change_pct:+.2f}% (${first_close:,.2f} -> ${last_close:,.2f})")

        return "\n".join(lines)
    except Exception as e:
        logger.error("get_klines failed for %s: %s", symbol, e)
        return f"Error fetching klines for {symbol}: {e}"


async def get_order_book(ctx: RunContext[AgentDeps], symbol: str, limit: int = 10) -> str:
    """Get order book (market depth) for a trading pair. Shows top bid/ask levels."""
    try:
        book = await ctx.deps.provider.get_order_book(symbol.upper(), min(limit, 100))
        lines = [f"Order book for {symbol.upper()} (top {len(book.bids)} levels):"]
        lines.append("  BIDS (buyers):")
        for bid in book.bids[:5]:
            lines.append(f"    ${bid.price:,.2f} | {bid.quantity:,.4f}")
        lines.append("  ASKS (sellers):")
        for ask in book.asks[:5]:
            lines.append(f"    ${ask.price:,.2f} | {ask.quantity:,.4f}")

        if book.bids and book.asks:
            spread = book.asks[0].price - book.bids[0].price
            spread_pct = (spread / book.asks[0].price) * 100
            lines.append(f"\n  Spread: ${spread:,.2f} ({spread_pct:.4f}%)")

        return "\n".join(lines)
    except Exception as e:
        logger.error("get_order_book failed for %s: %s", symbol, e)
        return f"Error fetching order book for {symbol}: {e}"


async def get_recent_trades(ctx: RunContext[AgentDeps], symbol: str, limit: int = 20) -> str:
    """Get most recent trades for a trading pair. Shows price, quantity, and buy/sell side."""
    try:
        trades = await ctx.deps.provider.get_recent_trades(symbol.upper(), min(limit, 100))
        if not trades:
            return f"No recent trades found for {symbol}"

        lines = [f"Recent trades for {symbol.upper()} (last {len(trades)}):"]
        buy_vol = 0.0
        sell_vol = 0.0
        for t in trades[-10:]:
            side = "SELL" if t.is_buyer_maker else "BUY"
            if t.is_buyer_maker:
                sell_vol += t.quantity
            else:
                buy_vol += t.quantity
            lines.append(f"  {t.time} | {side} ${t.price:,.2f} x {t.quantity:,.4f}")

        total = buy_vol + sell_vol
        buy_pct = (buy_vol / total * 100) if total else 0.0
        lines.append(f"\nBuy volume: {buy_pct:.1f}% | Sell volume: {100 - buy_pct:.1f}%")
        return "\n".join(lines)
    except Exception as e:
        logger.error("get_recent_trades failed for %s: %s", symbol, e)
        return f"Error fetching recent trades for {symbol}: {e}"


async def get_exchange_info(ctx: RunContext[AgentDeps]) -> str:
    """List currently tradeable spot symbols. Use to validate a symbol before querying it."""
    try:
        info = await ctx.deps.provider.get_exchange_info()
        majors = [s for s in info.trading_symbols if s.endswith("USDT")][:20]
        return (
            f"Binance Spot ({info.timezone}), {len(info.trading_symbols)} trading symbols. "
            f"Examples: {', '.join(majors)}"
        )
    except Exception as e:
        logger.error("get_exchange_info failed: %s", e)
        return f"Error fetching exchange info: {e}"


async def get_indicators(
    ctx: RunContext[AgentDeps],
    symbol: str,
    interval: str = "1h",
) -> str:
    """Compute deterministic indicators (SMA-20, EMA-20, RSI-14, volatility, support/resistance, volume) from klines."""
    try:
        klines = await ctx.deps.provider.get_klines(symbol.upper(), interval, 100)
        if len(klines) < 15:
            return f"Not enough kline data for {symbol} to compute indicators"

        c = closes(klines)
        sma20 = simple_moving_average(c, 20)
        ema20 = exponential_moving_average(c, 20)
        rsi14 = rsi(c, 14)
        vol = volatility_pct(c, 24)
        sr = support_resistance(klines)
        vs = volume_summary(klines)

        def fmt(v: float | None, suffix: str = "") -> str:
            return f"{v:,.2f}{suffix}" if v is not None else "n/a"

        return (
            f"Indicators for {symbol.upper()} ({interval}, {len(klines)} candles):\n"
            f"  SMA-20: ${fmt(sma20)} | EMA-20: ${fmt(ema20)}\n"
            f"  RSI-14: {fmt(rsi14)} | Volatility: {fmt(vol, '%')}\n"
            f"  Support: ${fmt(sr['support'])} | Resistance: ${fmt(sr['resistance'])}\n"
            f"  Volume avg: {fmt(vs['average'])} | latest: {fmt(vs['latest'])}"
            + (f" (x{vs['ratio']:.1f} avg)" if vs["ratio"] is not None else "")
        )
    except Exception as e:
        logger.error("get_indicators failed for %s: %s", symbol, e)
        return f"Error computing indicators for {symbol}: {e}"
