"""Binance connection status and environment information endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth.user_auth import current_user_dep
from app.binance.sub_account_service import is_sub_account_configured
from app.core.config import get_settings

router = APIRouter(prefix="/binance", tags=["binance"])


class BinanceStatusResponse(BaseModel):
    connected: bool
    environment: str  # "production" | "testnet"
    mode: str  # "live" | "sandbox"
    authenticated: bool
    api_credentials_configured: bool
    trading_enabled: bool
    sub_account_configured: bool
    testnet_auto_enabled: bool


@router.get("/status", response_model=BinanceStatusResponse)
async def binance_status(
    _user: dict = Depends(current_user_dep),
) -> BinanceStatusResponse:
    settings = get_settings()

    has_creds = bool(settings.binance_api_key and settings.binance_api_secret)
    is_testnet = settings.binance_is_testnet

    return BinanceStatusResponse(
        connected=has_creds or is_testnet,
        environment="testnet" if is_testnet else "production",
        mode="sandbox" if is_testnet else "live",
        authenticated=has_creds,
        api_credentials_configured=has_creds,
        trading_enabled=True,
        sub_account_configured=is_sub_account_configured(),
        testnet_auto_enabled=is_testnet and not settings.binance_testnet and not has_creds,
    )
