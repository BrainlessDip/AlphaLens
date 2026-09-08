"""Service layer wrapping binance-sdk-sub-account SDK.

Keeps SDK completely isolated from agent / frontend layers.
SDK is synchronous (requests.Session); every call is wrapped in asyncio.to_thread.
"""

from __future__ import annotations

import asyncio
import logging
from decimal import Decimal
from typing import Any

from binance_common.configuration import ConfigurationRestAPI
from binance_sdk_sub_account import (
    SubAccount,
    ClientError,
    ForbiddenError,
    UnauthorizedError,
    TooManyRequestsError,
)

from app.binance.sub_account_models import (
    DepositHistory,
    DepositRecord,
    FuturesAccount,
    FuturesAccountAsset,
    FuturesAccountSummary,
    FuturesAccountSummaryItem,
    FuturesPosition,
    FuturesPositionRisk,
    FuturesTransfer,
    MarginAccount,
    MarginAccountAsset,
    MarginAccountSummary,
    MarginAccountSummaryItem,
    SpotTransfer,
    SubAccountAsset,
    SubAccountAssets,
    SubAccountInfo,
    SubAccountSpotSummary,
    SubAccountStatus,
    UniversalTransfer,
)
from app.core.config import get_settings
from app.core.exceptions import BinanceAPIError

logger = logging.getLogger(__name__)


def _unwrap(response: Any, label: str) -> Any:
    """Extract data from SDK ApiResponse, raise on error."""
    if hasattr(response, "data"):
        return response.data
    raise BinanceAPIError(f"Unexpected response from Binance ({label})")


class SubAccountService:
    """Async wrapper around binance-sdk-sub-account."""

    def __init__(self) -> None:
        settings = get_settings()
        api_key = settings.binance_sub_account_api_key or settings.binance_api_key
        api_secret = (
            settings.binance_sub_account_api_secret or settings.binance_api_secret
        )

        if not api_key or not api_secret:
            raise BinanceAPIError(
                "Binance sub-account API credentials not configured. "
                "Set BINANCE_SUB_ACCOUNT_API_KEY and BINANCE_SUB_ACCOUNT_API_SECRET."
            )

        config = ConfigurationRestAPI(api_key=api_key, api_secret=api_secret)
        self._client = SubAccount(config)

    @property
    def _rest(self):
        return self._client.rest_api

    # ── Account ──────────────────────────────────────────────────

    async def get_sub_account_list(
        self,
        email: str | None = None,
        is_freeze: str | None = None,
        page: int | None = None,
        limit: int | None = None,
    ) -> list[SubAccountInfo]:
        try:
            resp = await asyncio.to_thread(
                self._rest.query_sub_account_list,
                email=email,
                is_freeze=is_freeze,
                page=page,
                limit=limit,
            )
            data = _unwrap(resp, "sub_account_list")
            accounts = getattr(data, "sub_accounts", None)
            if accounts is None:
                accounts = getattr(data, "subAccountList", []) or []
                # Try camelCase from raw dict responses
                if not accounts and hasattr(data, "subAccounts"):
                    accounts = getattr(data, "subAccounts", [])
            return [
                SubAccountInfo(
                    email=getattr(a, "email", "") or a.get("email", "")
                    if hasattr(a, "get")
                    else getattr(a, "email", ""),
                    is_trader=getattr(a, "isTrader", False),
                    is_futures_enabled=getattr(a, "isFuturesEnabled", False),
                    is_margin_enabled=getattr(a, "isMarginEnabled", False),
                    is_options_enabled=getattr(a, "isOptionsEnabled", False),
                    update_time=getattr(a, "updateTime", 0),
                )
                for a in (accounts or [])
            ]
        except BinanceAPIError:
            raise
        except (ClientError, ForbiddenError, UnauthorizedError) as e:
            raise BinanceAPIError(f"Binance auth error: {e}") from e
        except TooManyRequestsError as e:
            raise BinanceAPIError("Binance rate limit hit. Try again shortly.") from e
        except Exception as e:
            logger.error("get_sub_account_list failed: %s", e)
            raise BinanceAPIError(f"Failed to fetch sub-accounts: {e}") from e

    async def get_sub_accounts_status(
        self,
        email: str | None = None,
    ) -> list[SubAccountStatus]:
        try:
            resp = await asyncio.to_thread(
                self._rest.get_sub_accounts_status_on_margin_or_futures,
                email=email,
            )
            data = _unwrap(resp, "sub_accounts_status")
            items = (
                data
                if isinstance(data, list)
                else getattr(data, "status_list", []) or []
            )
            return [
                SubAccountStatus(
                    email=s.get("email", ""),
                    is_sub_account=s.get("isSubAccount", False),
                    is_margin_enabled=s.get("isMarginEnabled", False),
                    is_futures_enabled=s.get("isFuturesEnabled", False),
                    is_asset_enabled=s.get("isAssetEnabled", False),
                )
                for s in items
            ]
        except BinanceAPIError:
            raise
        except Exception as e:
            logger.error("get_sub_accounts_status failed: %s", e)
            raise BinanceAPIError(f"Failed to fetch sub-account statuses: {e}") from e

    async def get_sub_account_assets(self, email: str) -> SubAccountAssets:
        try:
            resp = await asyncio.to_thread(
                self._rest.query_sub_account_assets,
                email=email,
            )
            data = _unwrap(resp, "sub_account_assets")
            balances = getattr(data, "balances", []) or []
            assets = []
            for b in balances:
                free = Decimal(b.get("free", "0"))
                locked = Decimal(b.get("locked", "0"))
                assets.append(
                    SubAccountAsset(
                        asset=b.get("asset", ""),
                        free=free,
                        locked=locked,
                        total=free + locked,
                    )
                )
            return SubAccountAssets(balances=assets)
        except BinanceAPIError:
            raise
        except Exception as e:
            logger.error("get_sub_account_assets failed for %s: %s", email, e)
            raise BinanceAPIError(f"Failed to fetch sub-account assets: {e}") from e

    async def get_sub_account_spot_assets_summary(
        self,
        email: str | None = None,
        page: int | None = None,
        size: int | None = None,
    ) -> SubAccountSpotSummary:
        try:
            resp = await asyncio.to_thread(
                self._rest.query_sub_account_spot_assets_summary,
                email=email,
                page=page,
                size=size,
            )
            data = _unwrap(resp, "spot_assets_summary")
            return SubAccountSpotSummary(
                total_freeze_btc=Decimal(
                    str(getattr(data, "totalFreezeBtc", "0") or "0")
                ),
                total_freeze_usdt=Decimal(
                    str(getattr(data, "totalFreezeUsdt", "0") or "0")
                ),
                total_net_asset_btc=Decimal(
                    str(getattr(data, "totalNetAssetBtc", "0") or "0")
                ),
                total_net_asset_usdt=Decimal(
                    str(getattr(data, "totalNetAssetUsdt", "0") or "0")
                ),
            )
        except BinanceAPIError:
            raise
        except Exception as e:
            logger.error("get_sub_account_spot_assets_summary failed: %s", e)
            raise BinanceAPIError(f"Failed to fetch spot assets summary: {e}") from e

    async def get_sub_account_transaction_statistics(
        self,
        email: str | None = None,
    ) -> dict:
        try:
            resp = await asyncio.to_thread(
                self._rest.query_sub_account_transaction_statistics,
                email=email,
            )
            return _unwrap(resp, "transaction_statistics")
        except BinanceAPIError:
            raise
        except Exception as e:
            logger.error("get_sub_account_transaction_statistics failed: %s", e)
            raise BinanceAPIError(f"Failed to fetch transaction statistics: {e}") from e

    # ── Futures ──────────────────────────────────────────────────

    async def get_futures_account(self, email: str) -> FuturesAccount:
        try:
            resp = await asyncio.to_thread(
                self._rest.get_detail_on_sub_accounts_futures_account,
                email=email,
            )
            data = _unwrap(resp, "futures_account")
            assets_raw = getattr(data, "assets", []) or []
            assets = [
                FuturesAccountAsset(
                    asset=a.get("asset", ""),
                    wallet_balance=Decimal(str(a.get("walletBalance", "0"))),
                    unrealized_profit=Decimal(str(a.get("unrealizedProfit", "0"))),
                    margin_balance=Decimal(str(a.get("marginBalance", "0"))),
                    available_balance=Decimal(str(a.get("availableBalance", "0"))),
                    cross_pnl=Decimal(str(a.get("crossUnPnl", "0"))),
                )
                for a in assets_raw
            ]
            return FuturesAccount(
                total_wallet_balance=Decimal(
                    str(getattr(data, "totalWalletBalance", "0") or "0")
                ),
                total_unrealized_profit=Decimal(
                    str(getattr(data, "totalUnrealizedProfit", "0") or "0")
                ),
                total_margin_balance=Decimal(
                    str(getattr(data, "totalMarginBalance", "0") or "0")
                ),
                total_cross_wallet_balance=Decimal(
                    str(getattr(data, "totalCrossWalletBalance", "0") or "0")
                ),
                available_balance=Decimal(
                    str(getattr(data, "availableBalance", "0") or "0")
                ),
                max_withdraw_amount=Decimal(
                    str(getattr(data, "maxWithdrawAmount", "0") or "0")
                ),
                assets=assets,
            )
        except BinanceAPIError:
            raise
        except Exception as e:
            logger.error("get_futures_account failed for %s: %s", email, e)
            raise BinanceAPIError(f"Failed to fetch futures account: {e}") from e

    async def get_futures_account_v2(self, email: str, futures_type: int = 1) -> dict:
        try:
            resp = await asyncio.to_thread(
                self._rest.get_detail_on_sub_accounts_futures_account_v2,
                email=email,
                futures_type=futures_type,
            )
            return _unwrap(resp, "futures_account_v2")
        except BinanceAPIError:
            raise
        except Exception as e:
            logger.error("get_futures_account_v2 failed for %s: %s", email, e)
            raise BinanceAPIError(f"Failed to fetch futures account v2: {e}") from e

    async def get_futures_position_risk(self, email: str) -> FuturesPositionRisk:
        try:
            resp = await asyncio.to_thread(
                self._rest.get_futures_position_risk_of_sub_account,
                email=email,
            )
            data = _unwrap(resp, "futures_position_risk")
            items = data if isinstance(data, list) else []
            positions = [
                FuturesPosition(
                    symbol=p.get("symbol", ""),
                    position_amount=Decimal(str(p.get("positionAmt", "0"))),
                    entry_price=Decimal(str(p.get("entryPrice", "0"))),
                    mark_price=Decimal(str(p.get("markPrice", "0"))),
                    unrealized_profit=Decimal(str(p.get("unRealizedProfit", "0"))),
                    leverage=int(p.get("leverage", 1)),
                    position_side=p.get("positionSide", "BOTH"),
                )
                for p in items
            ]
            return FuturesPositionRisk(positions=positions)
        except BinanceAPIError:
            raise
        except Exception as e:
            logger.error("get_futures_position_risk failed for %s: %s", email, e)
            raise BinanceAPIError(f"Failed to fetch futures position risk: {e}") from e

    async def get_futures_account_summary(
        self,
        page: int = 1,
        limit: int = 10,
    ) -> FuturesAccountSummary:
        try:
            resp = await asyncio.to_thread(
                self._rest.get_summary_of_sub_accounts_futures_account,
                page=page,
                limit=limit,
            )
            data = _unwrap(resp, "futures_account_summary")
            items = (
                getattr(data, "sub_account_list", None)
                or getattr(data, "subAccountList", [])
                or []
            )
            sub_accounts = [
                FuturesAccountSummaryItem(
                    sub_account_id=getattr(s, "subAccountId", ""),
                    total_margin_balance=Decimal(
                        str(getattr(s, "totalMarginBalance", "0"))
                    ),
                    total_unrealized_profit=Decimal(
                        str(getattr(s, "totalUnrealizedProfit", "0"))
                    ),
                    total_wallet_balance=Decimal(
                        str(getattr(s, "totalWalletBalance", "0"))
                    ),
                )
                for s in items
            ]
            return FuturesAccountSummary(
                total_account_number=getattr(data, "totalAccountNumber", 0) or 0,
                total_wallet_balance=Decimal(
                    str(getattr(data, "totalWalletBalance", "0") or "0")
                ),
                total_unrealized_profit=Decimal(
                    str(getattr(data, "totalUnrealizedProfit", "0") or "0")
                ),
                total_margin_balance=Decimal(
                    str(getattr(data, "totalMarginBalance", "0") or "0")
                ),
                asset=getattr(data, "asset", "USDT") or "USDT",
                sub_accounts=sub_accounts,
            )
        except BinanceAPIError:
            raise
        except Exception as e:
            logger.error("get_futures_account_summary failed: %s", e)
            raise BinanceAPIError(
                f"Failed to fetch futures account summary: {e}"
            ) from e

    # ── Margin ───────────────────────────────────────────────────

    async def get_margin_account(self, email: str) -> MarginAccount:
        try:
            resp = await asyncio.to_thread(
                self._rest.get_detail_on_sub_accounts_margin_account,
                email=email,
            )
            data = _unwrap(resp, "margin_account")
            assets_raw = getattr(data, "userAssets", []) or []
            user_assets = [
                MarginAccountAsset(
                    asset=a.get("asset", ""),
                    free=Decimal(str(a.get("free", "0"))),
                    locked=Decimal(str(a.get("locked", "0"))),
                    borrowed=Decimal(str(a.get("borrowed", "0"))),
                    interest=Decimal(str(a.get("interest", "0"))),
                    net_asset=Decimal(str(a.get("netAsset", "0"))),
                )
                for a in assets_raw
            ]
            return MarginAccount(
                total_net_asset=Decimal(
                    str(getattr(data, "totalNetAsset", "0") or "0")
                ),
                total_asset_in_btc=Decimal(
                    str(getattr(data, "totalNetAssetOfBtc", "0") or "0")
                ),
                total_liability_in_btc=Decimal(
                    str(getattr(data, "totalLiabilityOfBtc", "0") or "0")
                ),
                total_collateral_value_in_usdt=Decimal(
                    str(getattr(data, "totalCollateralValueInUsdt", "0") or "0")
                ),
                user_assets=user_assets,
            )
        except BinanceAPIError:
            raise
        except Exception as e:
            logger.error("get_margin_account failed for %s: %s", email, e)
            raise BinanceAPIError(f"Failed to fetch margin account: {e}") from e

    async def get_margin_account_summary(self) -> MarginAccountSummary:
        try:
            resp = await asyncio.to_thread(
                self._rest.get_summary_of_sub_accounts_margin_account,
            )
            data = _unwrap(resp, "margin_account_summary")
            items = getattr(data, "subAccountList", []) or []
            sub_accounts = [
                MarginAccountSummaryItem(
                    sub_account_id=s.get("subAccountId", ""),
                    total_net_asset=Decimal(str(s.get("totalNetAsset", "0"))),
                    borrowed=Decimal(str(s.get("borrowed", "0"))),
                    free=Decimal(str(s.get("free", "0"))),
                    interest=Decimal(str(s.get("interest", "0"))),
                )
                for s in items
            ]
            return MarginAccountSummary(
                total_net_asset=Decimal(
                    str(getattr(data, "totalNetAsset", "0") or "0")
                ),
                sub_accounts=sub_accounts,
            )
        except BinanceAPIError:
            raise
        except Exception as e:
            logger.error("get_margin_account_summary failed: %s", e)
            raise BinanceAPIError(f"Failed to fetch margin account summary: {e}") from e

    # ── Transfer history ─────────────────────────────────────────

    async def get_spot_transfer_history(
        self,
        from_email: str | None = None,
        to_email: str | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
        page: int | None = None,
        limit: int | None = None,
    ) -> list[SpotTransfer]:
        try:
            resp = await asyncio.to_thread(
                self._rest.query_sub_account_spot_asset_transfer_history,
                from_email=from_email,
                to_email=to_email,
                start_time=start_time,
                end_time=end_time,
                page=page,
                limit=limit,
            )
            data = _unwrap(resp, "spot_transfer_history")
            items = data if isinstance(data, list) else []
            return [
                SpotTransfer(
                    timestamp=t.get("timestamp", 0),
                    asset=t.get("asset", ""),
                    amount=Decimal(str(t.get("qty", "0"))),
                    from_account=t.get("fromEmail", ""),
                    to_account=t.get("toEmail", ""),
                )
                for t in items
            ]
        except BinanceAPIError:
            raise
        except Exception as e:
            logger.error("get_spot_transfer_history failed: %s", e)
            raise BinanceAPIError(f"Failed to fetch spot transfer history: {e}") from e

    async def get_futures_transfer_history(
        self,
        email: str,
        futures_type: int = 1,
        start_time: int | None = None,
        end_time: int | None = None,
        page: int | None = None,
        limit: int | None = None,
    ) -> list[FuturesTransfer]:
        try:
            resp = await asyncio.to_thread(
                self._rest.query_sub_account_futures_asset_transfer_history,
                email=email,
                futures_type=futures_type,
                start_time=start_time,
                end_time=end_time,
                page=page,
                limit=limit,
            )
            data = _unwrap(resp, "futures_transfer_history")
            items = getattr(data, "transfers", []) or []
            return [
                FuturesTransfer(
                    timestamp=t.get("timestamp", 0),
                    asset=t.get("asset", ""),
                    amount=Decimal(str(t.get("qty", "0"))),
                    from_account=str(t.get("fromEmail", t.get("fromAccount", ""))),
                    to_account=str(t.get("toEmail", t.get("toAccount", ""))),
                )
                for t in items
            ]
        except BinanceAPIError:
            raise
        except Exception as e:
            logger.error("get_futures_transfer_history failed: %s", e)
            raise BinanceAPIError(
                f"Failed to fetch futures transfer history: {e}"
            ) from e

    async def get_universal_transfer_history(
        self,
        from_email: str | None = None,
        to_email: str | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
        page: int | None = None,
        limit: int | None = None,
    ) -> list[UniversalTransfer]:
        try:
            resp = await asyncio.to_thread(
                self._rest.query_universal_transfer_history,
                from_email=from_email,
                to_email=to_email,
                start_time=start_time,
                end_time=end_time,
                page=page,
                limit=limit,
            )
            data = _unwrap(resp, "universal_transfer_history")
            items = getattr(data, "result", []) or []
            return [
                UniversalTransfer(
                    timestamp=t.get("timestamp", 0),
                    asset=t.get("asset", ""),
                    amount=Decimal(str(t.get("qty", "0"))),
                    from_account=str(t.get("fromAccountType", "")),
                    to_account=str(t.get("toAccountType", "")),
                    status=str(t.get("status", "")),
                )
                for t in items
            ]
        except BinanceAPIError:
            raise
        except Exception as e:
            logger.error("get_universal_transfer_history failed: %s", e)
            raise BinanceAPIError(
                f"Failed to fetch universal transfer history: {e}"
            ) from e

    # ── Deposit history ──────────────────────────────────────────

    async def get_deposit_history(
        self,
        email: str,
        coin: str | None = None,
        status: int | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int | None = None,
    ) -> DepositHistory:
        try:
            resp = await asyncio.to_thread(
                self._rest.get_sub_account_deposit_history,
                email=email,
                coin=coin,
                status=status,
                start_time=start_time,
                end_time=end_time,
                limit=limit,
            )
            data = _unwrap(resp, "deposit_history")
            items = data if isinstance(data, list) else []
            deposits = [
                DepositRecord(
                    timestamp=d.get("insertTime", 0),
                    coin=d.get("coin", ""),
                    amount=Decimal(str(d.get("amount", "0"))),
                    network=d.get("network", ""),
                    address=d.get("address", ""),
                    status=d.get("status", 0),
                    tx_id=d.get("txId", ""),
                )
                for d in items
            ]
            return DepositHistory(deposits=deposits)
        except BinanceAPIError:
            raise
        except Exception as e:
            logger.error("get_deposit_history failed for %s: %s", email, e)
            raise BinanceAPIError(f"Failed to fetch deposit history: {e}") from e


# ── Singleton ────────────────────────────────────────────────────

_service_instance: SubAccountService | None = None


def get_sub_account_service() -> SubAccountService:
    """Lazy singleton for the sub-account service."""
    global _service_instance
    if _service_instance is None:
        _service_instance = SubAccountService()
    return _service_instance


def is_sub_account_configured() -> bool:
    """Check if sub-account credentials are configured."""
    settings = get_settings()
    return bool(
        settings.binance_sub_account_api_key or settings.binance_api_key
    ) and bool(settings.binance_sub_account_api_secret or settings.binance_api_secret)
