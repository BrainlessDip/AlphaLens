import logging
from decimal import Decimal

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
from app.agent.dependencies import AgentDeps

logger = logging.getLogger(__name__)


def tool_label(tool_name: str, args: dict | None = None) -> str:
    """Safe, human-readable label for a tool call. Only name + safe scalar args."""
    args = args or {}
    symbol = str(args.get("symbol", "")).upper() or None
    interval = str(args.get("interval", "") or "")
    labels = {
        "get_ticker": f"Getting {symbol} price" if symbol else "Getting current price",
        "get_24h_stats": f"Checking {symbol} 24h statistics" if symbol else "Checking 24h statistics",
        "get_klines": f"Reading {symbol} {interval} candles".strip() if symbol else "Reading market candles",
        "get_order_book": f"Checking {symbol} order book" if symbol else "Checking order book",
        "get_recent_trades": f"Reading {symbol} recent trades" if symbol else "Reading recent trades",
        "get_exchange_info": "Checking available symbols",
        "get_indicators": f"Analyzing {symbol} indicators".strip() if symbol else "Analyzing indicators",
    }
    # Sub-account tools
    email = str(args.get("email", "") or "")
    short_email = email.split("@")[0] if email else ""
    sub_labels = {
        "get_sub_accounts": "Listing sub-accounts",
        "get_sub_account_assets": f"Checking {short_email} balances" if short_email else "Checking sub-account balances",
        "get_sub_account_spot_summary": "Fetching spot assets summary",
        "get_sub_account_futures_account": f"Checking {short_email} futures" if short_email else "Checking futures account",
        "get_sub_account_futures_positions": f"Checking {short_email} futures positions" if short_email else "Checking futures positions",
        "get_sub_account_futures_summary": "Fetching futures account summary",
        "get_sub_account_margin_account": f"Checking {short_email} margin" if short_email else "Checking margin account",
        "get_sub_account_margin_summary": "Fetching margin account summary",
        "get_sub_account_transfer_history": "Fetching spot transfer history",
        "get_sub_account_futures_transfer_history": "Fetching futures transfer history",
        "get_sub_account_universal_transfer_history": "Fetching universal transfer history",
        "get_sub_account_deposit_history": f"Fetching {short_email} deposit history" if short_email else "Fetching deposit history",
    }
    return sub_labels.get(tool_name, labels.get(tool_name, f"Running {tool_name}"))


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


# ── Sub-Account Tools ────────────────────────────────────────────────


async def get_sub_accounts(ctx: RunContext[AgentDeps]) -> str:
    """List all Binance sub-accounts under the master account.
    Use when the user asks about their sub-accounts, wants to see all sub-accounts,
    or needs to know sub-account emails/status."""
    if ctx.deps.sub_account is None:
        return "Sub-account API is not configured. Set BINANCE_SUB_ACCOUNT_API_KEY and BINANCE_SUB_ACCOUNT_API_SECRET."
    try:
        accounts = await ctx.deps.sub_account.get_sub_account_list()
        if not accounts:
            return "No sub-accounts found."
        lines = [f"Sub-Accounts ({len(accounts)} total):"]
        for a in accounts:
            flags = []
            if a.is_futures_enabled:
                flags.append("Futures")
            if a.is_margin_enabled:
                flags.append("Margin")
            if a.is_options_enabled:
                flags.append("Options")
            lines.append(f"  {a.email} — {', '.join(flags) if flags else 'Spot only'}")
        return "\n".join(lines)
    except Exception as e:
        logger.error("get_sub_accounts failed: %s", e)
        return f"Error listing sub-accounts: {e}"


async def get_sub_account_assets(ctx: RunContext[AgentDeps], email: str) -> str:
    """Get spot assets/balances for a specific Binance sub-account.
    Use when the user asks about a sub-account's holdings, balances, or portfolio assets.
    The email parameter is the sub-account email address."""
    if ctx.deps.sub_account is None:
        return "Sub-account API is not configured."
    try:
        result = await ctx.deps.sub_account.get_sub_account_assets(email=email)
        if not result.balances:
            return f"No assets found for sub-account {email}."
        lines = [f"Assets for {email}:"]
        for asset in result.balances:
            lines.append(f"  {asset.asset}: {asset.free} (available) + {asset.locked} (locked) = {asset.total} (total)")
        return "\n".join(lines)
    except Exception as e:
        logger.error("get_sub_account_assets failed for %s: %s", email, e)
        return f"Error fetching assets for {email}: {e}"


async def get_sub_account_spot_summary(
    ctx: RunContext[AgentDeps], email: str | None = None,
) -> str:
    """Get BTC-valued spot assets summary for a sub-account or all sub-accounts.
    Use when the user asks about total portfolio value, BTC-equivalent holdings,
    or wants a high-level view of spot asset distribution."""
    if ctx.deps.sub_account is None:
        return "Sub-account API is not configured."
    try:
        result = await ctx.deps.sub_account.get_sub_account_spot_assets_summary(email=email)
        return (
            f"Spot Assets Summary:\n"
            f"  Net Asset: {result.total_net_asset_btc} BTC / {result.total_net_asset_usdt} USDT\n"
            f"  Frozen: {result.total_freeze_btc} BTC / {result.total_freeze_usdt} USDT"
        )
    except Exception as e:
        logger.error("get_sub_account_spot_summary failed: %s", e)
        return f"Error fetching spot summary: {e}"


async def get_sub_account_futures_account(ctx: RunContext[AgentDeps], email: str) -> str:
    """Get futures account details for a sub-account including wallet balance,
    unrealized PnL, margin balance, and available balance.
    Use when the user asks about a sub-account's futures trading status, margin, or PnL."""
    if ctx.deps.sub_account is None:
        return "Sub-account API is not configured."
    try:
        result = await ctx.deps.sub_account.get_futures_account(email=email)
        lines = [f"Futures Account for {email}:"]
        lines.append(f"  Wallet Balance: {result.total_wallet_balance} USDT")
        lines.append(f"  Unrealized PnL: {result.total_unrealized_profit} USDT")
        lines.append(f"  Margin Balance: {result.total_margin_balance} USDT")
        lines.append(f"  Available: {result.available_balance} USDT")
        for a in result.assets:
            lines.append(f"  {a.asset}: wallet={a.wallet_balance}, available={a.available_balance}")
        return "\n".join(lines)
    except Exception as e:
        logger.error("get_sub_account_futures_account failed for %s: %s", email, e)
        return f"Error fetching futures account for {email}: {e}"


async def get_sub_account_futures_positions(ctx: RunContext[AgentDeps], email: str) -> str:
    """Get futures position risk for a sub-account including all open positions,
    entry prices, mark prices, unrealized PnL, and leverage.
    Use when the user asks about a sub-account's open futures positions, current exposure, or position details."""
    if ctx.deps.sub_account is None:
        return "Sub-account API is not configured."
    try:
        result = await ctx.deps.sub_account.get_futures_position_risk(email=email)
        if not result.positions:
            return f"No open futures positions for {email}."
        lines = [f"Futures Positions for {email}:"]
        for p in result.positions:
            lines.append(
                f"  {p.symbol}: qty={p.position_amount}, entry={p.entry_price}, "
                f"mark={p.mark_price}, PnL={p.unrealized_profit}, "
                f"leverage={p.leverage}x, side={p.position_side}"
            )
        return "\n".join(lines)
    except Exception as e:
        logger.error("get_sub_account_futures_positions failed for %s: %s", email, e)
        return f"Error fetching futures positions for {email}: {e}"


async def get_sub_account_futures_summary(
    ctx: RunContext[AgentDeps], page: int = 1, limit: int = 10,
) -> str:
    """Get aggregated futures account summary across all sub-accounts.
    Use when the user wants a high-level view of all sub-accounts' futures wallets, total PnL, and margin balances."""
    if ctx.deps.sub_account is None:
        return "Sub-account API is not configured."
    try:
        result = await ctx.deps.sub_account.get_futures_account_summary(page=page, limit=limit)
        lines = [
            f"Futures Summary ({result.total_account_number} accounts):",
            f"  Total Wallet: {result.total_wallet_balance} {result.asset}",
            f"  Total Unrealized PnL: {result.total_unrealized_profit} {result.asset}",
            f"  Total Margin Balance: {result.total_margin_balance} {result.asset}",
        ]
        for s in result.sub_accounts:
            lines.append(f"  {s.sub_account_id}: wallet={s.total_wallet_balance}, PnL={s.total_unrealized_profit}")
        return "\n".join(lines)
    except Exception as e:
        logger.error("get_sub_account_futures_summary failed: %s", e)
        return f"Error fetching futures summary: {e}"


async def get_sub_account_margin_account(ctx: RunContext[AgentDeps], email: str) -> str:
    """Get margin account details for a sub-account including borrowed amounts,
    interest, net asset value, and per-asset breakdown.
    Use when the user asks about a sub-account's margin trading, borrows, or margin account status."""
    if ctx.deps.sub_account is None:
        return "Sub-account API is not configured."
    try:
        result = await ctx.deps.sub_account.get_margin_account(email=email)
        lines = [f"Margin Account for {email}:"]
        lines.append(f"  Total Net Asset: {result.total_net_asset} (≈ {result.total_asset_in_btc} BTC)")
        lines.append(f"  Total Liability: {result.total_liability_in_btc} BTC")
        lines.append(f"  Collateral (USDT): {result.total_collateral_value_in_usdt}")
        for a in result.user_assets:
            lines.append(f"  {a.asset}: free={a.free}, borrowed={a.borrowed}, interest={a.interest}, net={a.net_asset}")
        return "\n".join(lines)
    except Exception as e:
        logger.error("get_sub_account_margin_account failed for %s: %s", email, e)
        return f"Error fetching margin account for {email}: {e}"


async def get_sub_account_margin_summary(ctx: RunContext[AgentDeps]) -> str:
    """Get aggregated margin account summary across all sub-accounts.
    Use when the user wants a high-level view of all sub-accounts' margin balances and borrowing."""
    if ctx.deps.sub_account is None:
        return "Sub-account API is not configured."
    try:
        result = await ctx.deps.sub_account.get_margin_account_summary()
        lines = ["Margin Account Summary:"]
        lines.append(f"  Total Net Asset: {result.total_net_asset}")
        for s in result.sub_accounts:
            lines.append(f"  {s.sub_account_id}: net={s.total_net_asset}, borrowed={s.borrowed}, free={s.free}")
        return "\n".join(lines)
    except Exception as e:
        logger.error("get_sub_account_margin_summary failed: %s", e)
        return f"Error fetching margin summary: {e}"


async def get_sub_account_transfer_history(
    ctx: RunContext[AgentDeps],
    from_email: str | None = None,
    to_email: str | None = None,
    start_time: int | None = None,
    end_time: int | None = None,
    page: int | None = None,
    limit: int | None = None,
) -> str:
    """Get spot asset transfer history between master and sub-accounts.
    Use when the user asks about transfers between accounts, transfer history,
    or wants to see when assets moved between the master and sub-accounts.
    If fromEmail and toEmail are both omitted, records from master account are returned."""
    if ctx.deps.sub_account is None:
        return "Sub-account API is not configured."
    try:
        transfers = await ctx.deps.sub_account.get_spot_transfer_history(
            from_email=from_email, to_email=to_email,
            start_time=start_time, end_time=end_time, page=page, limit=limit,
        )
        if not transfers:
            return "No spot transfer history found."
        lines = ["Spot Transfer History:"]
        for t in transfers:
            lines.append(f"  {t.asset}: {t.amount} from {t.from_account} → {t.to_account}")
        return "\n".join(lines)
    except Exception as e:
        logger.error("get_sub_account_transfer_history failed: %s", e)
        return f"Error fetching transfer history: {e}"


async def get_sub_account_futures_transfer_history(
    ctx: RunContext[AgentDeps],
    email: str,
    futures_type: int = 1,
    start_time: int | None = None,
    end_time: int | None = None,
    page: int | None = None,
    limit: int | None = None,
) -> str:
    """Get futures internal transfer history for a sub-account.
    Use when the user asks about futures transfers, funding transfers,
    or asset movements between spot and futures wallets.
    futures_type: 1=USDT-margined, 2=Coin-margined."""
    if ctx.deps.sub_account is None:
        return "Sub-account API is not configured."
    try:
        transfers = await ctx.deps.sub_account.get_futures_transfer_history(
            email=email, futures_type=futures_type,
            start_time=start_time, end_time=end_time, page=page, limit=limit,
        )
        if not transfers:
            return f"No futures transfer history found for {email}."
        lines = [f"Futures Transfer History for {email}:"]
        for t in transfers:
            lines.append(f"  {t.asset}: {t.amount} from {t.from_account} → {t.to_account}")
        return "\n".join(lines)
    except Exception as e:
        logger.error("get_sub_account_futures_transfer_history failed: %s", e)
        return f"Error fetching futures transfer history: {e}"


async def get_sub_account_universal_transfer_history(
    ctx: RunContext[AgentDeps],
    from_email: str | None = None,
    to_email: str | None = None,
    start_time: int | None = None,
    end_time: int | None = None,
    page: int | None = None,
    limit: int | None = None,
) -> str:
    """Get universal transfer history across all account types.
    Use when the user asks about universal transfers, cross-account transfers,
    or wants to see all asset movements regardless of account type.
    Query time range must be less than 7 days."""
    if ctx.deps.sub_account is None:
        return "Sub-account API is not configured."
    try:
        transfers = await ctx.deps.sub_account.get_universal_transfer_history(
            from_email=from_email, to_email=to_email,
            start_time=start_time, end_time=end_time, page=page, limit=limit,
        )
        if not transfers:
            return "No universal transfer history found."
        lines = ["Universal Transfer History:"]
        for t in transfers:
            lines.append(f"  {t.asset}: {t.amount} from {t.from_account} → {t.to_account} ({t.status})")
        return "\n".join(lines)
    except Exception as e:
        logger.error("get_sub_account_universal_transfer_history failed: %s", e)
        return f"Error fetching universal transfer history: {e}"


async def get_sub_account_deposit_history(
    ctx: RunContext[AgentDeps],
    email: str,
    coin: str | None = None,
    start_time: int | None = None,
    end_time: int | None = None,
    limit: int | None = None,
) -> str:
    """Get deposit history for a sub-account.
    Use when the user asks about deposits into a sub-account, deposit status,
    or wants to know if funds were deposited."""
    if ctx.deps.sub_account is None:
        return "Sub-account API is not configured."
    try:
        result = await ctx.deps.sub_account.get_deposit_history(
            email=email, coin=coin, start_time=start_time, end_time=end_time, limit=limit,
        )
        if not result.deposits:
            return f"No deposit history found for {email}."
        status_map = {0: "pending", 1: "success", 6: "credited", 7: "wrong", 8: "waiting"}
        lines = [f"Deposit History for {email}:"]
        for d in result.deposits:
            status_str = status_map.get(d.status, f"status={d.status}")
            lines.append(f"  {d.coin}: {d.amount} ({status_str}) — {d.network} txid={d.tx_id[:16] if d.tx_id else 'n/a'}...")
        return "\n".join(lines)
    except Exception as e:
        logger.error("get_sub_account_deposit_history failed for %s: %s", email, e)
        return f"Error fetching deposit history for {email}: {e}"
