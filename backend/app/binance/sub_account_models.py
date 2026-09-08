"""Pydantic models for Binance Sub-Account data exposed to agent/tools/frontend."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


# ── Account ──────────────────────────────────────────────────────────


class SubAccountInfo(BaseModel):
    email: str
    is_trader: bool = False
    is_futures_enabled: bool = False
    is_margin_enabled: bool = False
    is_options_enabled: bool = False
    update_time: int = 0


class SubAccountAsset(BaseModel):
    asset: str
    free: Decimal = Decimal("0")
    locked: Decimal = Decimal("0")
    total: Decimal = Decimal("0")


class SubAccountAssets(BaseModel):
    balances: list[SubAccountAsset] = Field(default_factory=list)


class SubAccountStatus(BaseModel):
    email: str
    is_sub_account: bool = False
    is_margin_enabled: bool = False
    is_futures_enabled: bool = False
    is_asset_enabled: bool = False


# ── Futures ──────────────────────────────────────────────────────────


class FuturesAccountAsset(BaseModel):
    asset: str
    wallet_balance: Decimal = Decimal("0")
    unrealized_profit: Decimal = Decimal("0")
    margin_balance: Decimal = Decimal("0")
    available_balance: Decimal = Decimal("0")
    cross_pnl: Decimal = Decimal("0")


class FuturesAccount(BaseModel):
    total_wallet_balance: Decimal = Decimal("0")
    total_unrealized_profit: Decimal = Decimal("0")
    total_margin_balance: Decimal = Decimal("0")
    total_cross_wallet_balance: Decimal = Decimal("0")
    available_balance: Decimal = Decimal("0")
    max_withdraw_amount: Decimal = Decimal("0")
    assets: list[FuturesAccountAsset] = Field(default_factory=list)


class FuturesPosition(BaseModel):
    symbol: str
    position_amount: Decimal = Decimal("0")
    entry_price: Decimal = Decimal("0")
    mark_price: Decimal = Decimal("0")
    unrealized_profit: Decimal = Decimal("0")
    leverage: int = 1
    position_side: str = "BOTH"


class FuturesPositionRisk(BaseModel):
    positions: list[FuturesPosition] = Field(default_factory=list)


# ── Margin ───────────────────────────────────────────────────────────


class MarginAccountAsset(BaseModel):
    asset: str
    free: Decimal = Decimal("0")
    locked: Decimal = Decimal("0")
    borrowed: Decimal = Decimal("0")
    interest: Decimal = Decimal("0")
    net_asset: Decimal = Decimal("0")


class MarginAccount(BaseModel):
    total_net_asset: Decimal = Decimal("0")
    total_asset_in_btc: Decimal = Decimal("0")
    total_liability_in_btc: Decimal = Decimal("0")
    total_collateral_value_in_usdt: Decimal = Decimal("0")
    user_assets: list[MarginAccountAsset] = Field(default_factory=list)


# ── Summary ──────────────────────────────────────────────────────────


class SubAccountSpotSummary(BaseModel):
    total_freeze_btc: Decimal = Decimal("0")
    total_freeze_usdt: Decimal = Decimal("0")
    total_net_asset_btc: Decimal = Decimal("0")
    total_net_asset_usdt: Decimal = Decimal("0")


class FuturesAccountSummaryItem(BaseModel):
    sub_account_id: str
    total_margin_balance: Decimal = Decimal("0")
    total_unrealized_profit: Decimal = Decimal("0")
    total_wallet_balance: Decimal = Decimal("0")


class FuturesAccountSummary(BaseModel):
    total_account_number: int = 0
    total_wallet_balance: Decimal = Decimal("0")
    total_unrealized_profit: Decimal = Decimal("0")
    total_margin_balance: Decimal = Decimal("0")
    asset: str = "USDT"
    sub_accounts: list[FuturesAccountSummaryItem] = Field(default_factory=list)


class MarginAccountSummaryItem(BaseModel):
    sub_account_id: str
    total_net_asset: Decimal = Decimal("0")
    borrowed: Decimal = Decimal("0")
    free: Decimal = Decimal("0")
    interest: Decimal = Decimal("0")


class MarginAccountSummary(BaseModel):
    total_net_asset: Decimal = Decimal("0")
    sub_accounts: list[MarginAccountSummaryItem] = Field(default_factory=list)


# ── Transfer history ─────────────────────────────────────────────────


class SpotTransfer(BaseModel):
    timestamp: int = 0
    asset: str
    amount: Decimal = Decimal("0")
    from_account: str = ""
    to_account: str = ""


class FuturesTransfer(BaseModel):
    timestamp: int = 0
    asset: str
    amount: Decimal = Decimal("0")
    from_account: str = ""
    to_account: str = ""


class UniversalTransfer(BaseModel):
    timestamp: int = 0
    asset: str
    amount: Decimal = Decimal("0")
    from_account: str = ""
    to_account: str = ""
    status: str = ""


class SubAccountTransferHistory(BaseModel):
    transfers: list[SpotTransfer | FuturesTransfer | UniversalTransfer] = Field(
        default_factory=list
    )


# ── Deposit / Withdrawal ────────────────────────────────────────────


class DepositRecord(BaseModel):
    timestamp: int = 0
    coin: str
    amount: Decimal = Decimal("0")
    network: str = ""
    address: str = ""
    status: int = 0
    tx_id: str = ""


class DepositHistory(BaseModel):
    deposits: list[DepositRecord] = Field(default_factory=list)


# ── Pagination ───────────────────────────────────────────────────────


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=50, ge=1, le=500)


class TimeFilter(BaseModel):
    start_time: int | None = None
    end_time: int | None = None
