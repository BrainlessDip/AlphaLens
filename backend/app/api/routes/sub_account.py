"""REST endpoints for Binance Sub-Account data."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from app.auth.user_auth import current_user_dep
from app.binance.sub_account_service import (
    SubAccountService,
    get_sub_account_service,
    is_sub_account_configured,
)
from app.core.exceptions import BinanceAPIError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sub-account", tags=["sub-account"])


class SubAccountConfigResponse(BaseModel):
    configured: bool


class SubAccountErrorResponse(BaseModel):
    error: str


def _get_service() -> SubAccountService:
    if not is_sub_account_configured():
        raise BinanceAPIError(
            "Sub-account API is not configured. "
            "Set BINANCE_SUB_ACCOUNT_API_KEY and BINANCE_SUB_ACCOUNT_API_SECRET."
        )
    return get_sub_account_service()


# ── Config ───────────────────────────────────────────────────────────


@router.get("/config", response_model=SubAccountConfigResponse)
async def sub_account_config(
    _user: Any = Depends(current_user_dep),
) -> SubAccountConfigResponse:
    return SubAccountConfigResponse(configured=is_sub_account_configured())


# ── Account ──────────────────────────────────────────────────────────


@router.get("")
async def get_sub_account_list(
    email: str | None = Query(default=None),
    is_freeze: str | None = Query(default=None),
    page: int | None = Query(default=None, ge=1),
    limit: int | None = Query(default=None, ge=1, le=500),
    _user: Any = Depends(current_user_dep),
) -> Any:
    svc = _get_service()
    accounts = await svc.get_sub_account_list(
        email=email,
        is_freeze=is_freeze,
        page=page,
        limit=limit,
    )
    return [a.model_dump() for a in accounts]


@router.get("/status")
async def get_sub_accounts_status(
    email: str | None = Query(default=None),
    _user: Any = Depends(current_user_dep),
) -> Any:
    svc = _get_service()
    statuses = await svc.get_sub_accounts_status(email=email)
    return [s.model_dump() for s in statuses]


@router.get("/assets")
async def get_sub_account_assets(
    email: str = Query(..., description="Sub-account email"),
    _user: Any = Depends(current_user_dep),
) -> Any:
    svc = _get_service()
    result = await svc.get_sub_account_assets(email=email)
    return result.model_dump()


@router.get("/spot-summary")
async def get_sub_account_spot_summary(
    email: str | None = Query(default=None),
    page: int | None = Query(default=None, ge=1),
    size: int | None = Query(default=None, ge=1, le=500),
    _user: Any = Depends(current_user_dep),
) -> Any:
    svc = _get_service()
    result = await svc.get_sub_account_spot_assets_summary(
        email=email,
        page=page,
        size=size,
    )
    return result.model_dump()


@router.get("/transaction-statistics")
async def get_sub_account_transaction_statistics(
    email: str | None = Query(default=None),
    _user: Any = Depends(current_user_dep),
) -> Any:
    svc = _get_service()
    return await svc.get_sub_account_transaction_statistics(email=email)


# ── Futures ──────────────────────────────────────────────────────────


@router.get("/futures")
async def get_futures_account(
    email: str = Query(..., description="Sub-account email"),
    _user: Any = Depends(current_user_dep),
) -> Any:
    svc = _get_service()
    result = await svc.get_futures_account(email=email)
    return result.model_dump()


@router.get("/futures/positions")
async def get_futures_position_risk(
    email: str = Query(..., description="Sub-account email"),
    _user: Any = Depends(current_user_dep),
) -> Any:
    svc = _get_service()
    result = await svc.get_futures_position_risk(email=email)
    return result.model_dump()


@router.get("/futures/summary")
async def get_futures_account_summary(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=500),
    _user: Any = Depends(current_user_dep),
) -> Any:
    svc = _get_service()
    result = await svc.get_futures_account_summary(page=page, limit=limit)
    return result.model_dump()


# ── Margin ───────────────────────────────────────────────────────────


@router.get("/margin")
async def get_margin_account(
    email: str = Query(..., description="Sub-account email"),
    _user: Any = Depends(current_user_dep),
) -> Any:
    svc = _get_service()
    result = await svc.get_margin_account(email=email)
    return result.model_dump()


@router.get("/margin/summary")
async def get_margin_account_summary(
    _user: Any = Depends(current_user_dep),
) -> Any:
    svc = _get_service()
    result = await svc.get_margin_account_summary()
    return result.model_dump()


# ── Transfer history ─────────────────────────────────────────────────


@router.get("/transfers/spot")
async def get_spot_transfer_history(
    from_email: str | None = Query(default=None),
    to_email: str | None = Query(default=None),
    start_time: int | None = Query(default=None),
    end_time: int | None = Query(default=None),
    page: int | None = Query(default=None, ge=1),
    limit: int | None = Query(default=None, ge=1, le=500),
    _user: Any = Depends(current_user_dep),
) -> Any:
    svc = _get_service()
    transfers = await svc.get_spot_transfer_history(
        from_email=from_email,
        to_email=to_email,
        start_time=start_time,
        end_time=end_time,
        page=page,
        limit=limit,
    )
    return [t.model_dump() for t in transfers]


@router.get("/transfers/futures")
async def get_futures_transfer_history(
    email: str = Query(..., description="Sub-account email"),
    futures_type: int = Query(default=1, ge=1, le=2),
    start_time: int | None = Query(default=None),
    end_time: int | None = Query(default=None),
    page: int | None = Query(default=None, ge=1),
    limit: int | None = Query(default=None, ge=1, le=500),
    _user: Any = Depends(current_user_dep),
) -> Any:
    svc = _get_service()
    transfers = await svc.get_futures_transfer_history(
        email=email,
        futures_type=futures_type,
        start_time=start_time,
        end_time=end_time,
        page=page,
        limit=limit,
    )
    return [t.model_dump() for t in transfers]


@router.get("/transfers/universal")
async def get_universal_transfer_history(
    from_email: str | None = Query(default=None),
    to_email: str | None = Query(default=None),
    start_time: int | None = Query(default=None),
    end_time: int | None = Query(default=None),
    page: int | None = Query(default=None, ge=1),
    limit: int | None = Query(default=None, ge=1, le=500),
    _user: Any = Depends(current_user_dep),
) -> Any:
    svc = _get_service()
    transfers = await svc.get_universal_transfer_history(
        from_email=from_email,
        to_email=to_email,
        start_time=start_time,
        end_time=end_time,
        page=page,
        limit=limit,
    )
    return [t.model_dump() for t in transfers]


# ── Deposits ─────────────────────────────────────────────────────────


@router.get("/deposits")
async def get_deposit_history(
    email: str = Query(..., description="Sub-account email"),
    coin: str | None = Query(default=None),
    start_time: int | None = Query(default=None),
    end_time: int | None = Query(default=None),
    limit: int | None = Query(default=None, ge=1, le=500),
    _user: Any = Depends(current_user_dep),
) -> Any:
    svc = _get_service()
    result = await svc.get_deposit_history(
        email=email,
        coin=coin,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
    )
    return result.model_dump()
