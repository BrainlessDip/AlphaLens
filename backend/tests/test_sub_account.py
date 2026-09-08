"""Tests for Binance Sub-Account service, tools, and API routes."""
from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient


# ── Service Tests ────────────────────────────────────────────────────


@pytest.fixture
def mock_sdk():
    """Mock the binance-sdk-sub-account SubAccount class."""
    with patch("app.binance.sub_account_service.SubAccount") as MockSDK:
        sdk_instance = MagicMock()
        rest_api = MagicMock()
        sdk_instance.rest_api = rest_api
        MockSDK.return_value = sdk_instance
        yield rest_api


@pytest.fixture
def sub_account_service(mock_sdk):
    """Create a SubAccountService with mocked SDK."""
    with patch("app.binance.sub_account_service.get_settings") as mock_settings:
        mock_settings.return_value = SimpleNamespace(
            binance_sub_account_api_key="test-key",
            binance_sub_account_api_secret="test-secret",
            binance_api_key="",
            binance_api_secret="",
        )
        from app.binance.sub_account_service import SubAccountService
        svc = SubAccountService.__new__(SubAccountService)
        svc._client = MagicMock()
        svc._client.rest_api = mock_sdk
        return svc


@pytest.mark.asyncio
async def test_get_sub_account_list(sub_account_service, mock_sdk):
    mock_sdk.query_sub_account_list.return_value = SimpleNamespace(
        data=SimpleNamespace(
            sub_accounts=[
                SimpleNamespace(
                    email="test@test.com",
                    isTrader=True,
                    isFuturesEnabled=True,
                    isMarginEnabled=False,
                    isOptionsEnabled=False,
                    updateTime=1234567890,
                )
            ]
        )
    )
    result = await sub_account_service.get_sub_account_list()
    assert len(result) == 1
    assert result[0].email == "test@test.com"
    assert result[0].is_trader is True
    assert result[0].is_futures_enabled is True


@pytest.mark.asyncio
async def test_get_sub_account_assets(sub_account_service, mock_sdk):
    mock_sdk.query_sub_account_assets.return_value = SimpleNamespace(
        data=SimpleNamespace(
            balances=[
                {"asset": "BTC", "free": "0.5", "locked": "0.1"},
                {"asset": "USDT", "free": "1000", "locked": "0"},
            ]
        )
    )
    result = await sub_account_service.get_sub_account_assets(email="test@test.com")
    assert len(result.balances) == 2
    assert result.balances[0].asset == "BTC"
    assert result.balances[0].total == Decimal("0.6")
    assert result.balances[1].asset == "USDT"
    assert result.balances[1].total == Decimal("1000")


@pytest.mark.asyncio
async def test_get_futures_account(sub_account_service, mock_sdk):
    mock_sdk.get_detail_on_sub_accounts_futures_account.return_value = SimpleNamespace(
        data=SimpleNamespace(
            totalWalletBalance="10000",
            totalUnrealizedProfit="500",
            totalMarginBalance="10500",
            totalCrossWalletBalance="10000",
            availableBalance="8000",
            maxWithdrawAmount="7500",
            assets=[
                {
                    "asset": "USDT",
                    "walletBalance": "10000",
                    "unrealizedProfit": "500",
                    "marginBalance": "10500",
                    "availableBalance": "8000",
                    "crossUnPnl": "500",
                }
            ],
        )
    )
    result = await sub_account_service.get_futures_account(email="test@test.com")
    assert result.total_wallet_balance == Decimal("10000")
    assert result.total_unrealized_profit == Decimal("500")
    assert len(result.assets) == 1
    assert result.assets[0].asset == "USDT"


@pytest.mark.asyncio
async def test_get_futures_position_risk(sub_account_service, mock_sdk):
    mock_sdk.get_futures_position_risk_of_sub_account.return_value = SimpleNamespace(
        data=[
            {
                "symbol": "BTCUSDT",
                "positionAmt": "0.01",
                "entryPrice": "60000",
                "markPrice": "61000",
                "unRealizedProfit": "10",
                "leverage": "10",
                "positionSide": "LONG",
            }
        ]
    )
    result = await sub_account_service.get_futures_position_risk(email="test@test.com")
    assert len(result.positions) == 1
    assert result.positions[0].symbol == "BTCUSDT"
    assert result.positions[0].unrealized_profit == Decimal("10")


@pytest.mark.asyncio
async def test_get_margin_account(sub_account_service, mock_sdk):
    mock_sdk.get_detail_on_sub_accounts_margin_account.return_value = SimpleNamespace(
        data=SimpleNamespace(
            totalNetAsset="5000",
            totalNetAssetOfBtc="0.08",
            totalLiabilityOfBtc="0.01",
            totalCollateralValueInUsdt="4500",
            userAssets=[
                {
                    "asset": "BTC",
                    "free": "0.05",
                    "locked": "0",
                    "borrowed": "0.01",
                    "interest": "0.0001",
                    "netAsset": "0.04",
                }
            ],
        )
    )
    result = await sub_account_service.get_margin_account(email="test@test.com")
    assert result.total_net_asset == Decimal("5000")
    assert len(result.user_assets) == 1
    assert result.user_assets[0].asset == "BTC"


@pytest.mark.asyncio
async def test_get_spot_transfer_history(sub_account_service, mock_sdk):
    mock_sdk.query_sub_account_spot_asset_transfer_history.return_value = SimpleNamespace(
        data=[
            {
                "timestamp": 1234567890,
                "asset": "BTC",
                "qty": "0.1",
                "fromEmail": "master@test.com",
                "toEmail": "sub@test.com",
            }
        ]
    )
    result = await sub_account_service.get_spot_transfer_history(
        from_email="master@test.com",
    )
    assert len(result) == 1
    assert result[0].asset == "BTC"
    assert result[0].amount == Decimal("0.1")
    assert result[0].from_account == "master@test.com"


@pytest.mark.asyncio
async def test_get_deposit_history(sub_account_service, mock_sdk):
    mock_sdk.get_sub_account_deposit_history.return_value = SimpleNamespace(
        data=[
            {
                "insertTime": 1234567890,
                "coin": "USDT",
                "amount": "100",
                "network": "TRX",
                "address": "Txxx",
                "status": 1,
                "txId": "tx123",
            }
        ]
    )
    result = await sub_account_service.get_deposit_history(email="test@test.com")
    assert len(result.deposits) == 1
    assert result.deposits[0].coin == "USDT"
    assert result.deposits[0].amount == Decimal("100")


@pytest.mark.asyncio
async def test_get_spot_assets_summary(sub_account_service, mock_sdk):
    mock_sdk.query_sub_account_spot_assets_summary.return_value = SimpleNamespace(
        data=SimpleNamespace(
            totalFreezeBtc="0.01",
            totalFreezeUsdt="600",
            totalNetAssetBtc="0.5",
            totalNetAssetUsdt="30000",
        )
    )
    result = await sub_account_service.get_sub_account_spot_assets_summary()
    assert result.total_net_asset_btc == Decimal("0.5")
    assert result.total_net_asset_usdt == Decimal("30000")


@pytest.mark.asyncio
async def test_get_futures_account_summary(sub_account_service, mock_sdk):
    mock_sdk.get_summary_of_sub_accounts_futures_account.return_value = SimpleNamespace(
        data=SimpleNamespace(
            totalAccountNumber=2,
            totalWalletBalance="20000",
            totalUnrealizedProfit="1000",
            totalMarginBalance="21000",
            asset="USDT",
            sub_account_list=[
                SimpleNamespace(
                    subAccountId="sub1@test.com",
                    totalMarginBalance="10500",
                    totalUnrealizedProfit="500",
                    totalWalletBalance="10000",
                )
            ],
        )
    )
    result = await sub_account_service.get_futures_account_summary()
    assert result.total_account_number == 2
    assert result.total_wallet_balance == Decimal("20000")
    assert len(result.sub_accounts) == 1


# ── Config check ─────────────────────────────────────────────────────


def test_is_sub_account_configured():
    from app.binance.sub_account_service import is_sub_account_configured
    with patch("app.binance.sub_account_service.get_settings") as mock_settings:
        mock_settings.return_value = SimpleNamespace(
            binance_sub_account_api_key="key",
            binance_sub_account_api_secret="secret",
            binance_api_key="",
            binance_api_secret="",
        )
        assert is_sub_account_configured() is True

    with patch("app.binance.sub_account_service.get_settings") as mock_settings:
        mock_settings.return_value = SimpleNamespace(
            binance_sub_account_api_key="",
            binance_sub_account_api_secret="",
            binance_api_key="",
            binance_api_secret="",
        )
        assert is_sub_account_configured() is False


def test_is_sub_account_configured_fallback():
    """Should fall back to generic Binance API key if sub-account key not set."""
    from app.binance.sub_account_service import is_sub_account_configured
    with patch("app.binance.sub_account_service.get_settings") as mock_settings:
        mock_settings.return_value = SimpleNamespace(
            binance_sub_account_api_key="",
            binance_sub_account_api_secret="",
            binance_api_key="fallback-key",
            binance_api_secret="fallback-secret",
        )
        assert is_sub_account_configured() is True


# ── API Route Tests ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_sub_account_config_endpoint(client: AsyncClient, auth_headers: dict):
    with patch("app.api.routes.sub_account.is_sub_account_configured", return_value=False):
        resp = await client.get("/api/v1/sub-account/config", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["configured"] is False


@pytest.mark.asyncio
async def test_sub_account_config_requires_auth(client: AsyncClient):
    resp = await client.get("/api/v1/sub-account/config")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_sub_account_list_requires_config(client: AsyncClient, auth_headers: dict):
    with patch("app.api.routes.sub_account.is_sub_account_configured", return_value=False):
        resp = await client.get("/api/v1/sub-account", headers=auth_headers)
        assert resp.status_code == 502  # BinanceAPIError


@pytest.mark.asyncio
async def test_sub_account_assets_requires_email(client: AsyncClient, auth_headers: dict):
    resp = await client.get("/api/v1/sub-account/assets", headers=auth_headers)
    assert resp.status_code == 422  # Missing required query param


@pytest.mark.asyncio
async def test_sub_account_list_endpoint(client: AsyncClient, auth_headers: dict):
    mock_svc = AsyncMock()
    mock_svc.get_sub_account_list.return_value = [
        SimpleNamespace(model_dump=lambda: {"email": "test@test.com", "is_trader": False, "is_futures_enabled": True, "is_margin_enabled": False, "is_options_enabled": False, "update_time": 0})
    ]

    with (
        patch("app.api.routes.sub_account.is_sub_account_configured", return_value=True),
        patch("app.api.routes.sub_account.get_sub_account_service", return_value=mock_svc),
    ):
        resp = await client.get("/api/v1/sub-account", headers=auth_headers)
        assert resp.status_code == 200


@pytest.mark.asyncio
async def test_sub_account_futures_endpoint(client: AsyncClient, auth_headers: dict):
    mock_svc = AsyncMock()
    mock_svc.get_futures_account.return_value = SimpleNamespace(
        model_dump=lambda: {
            "total_wallet_balance": "10000",
            "total_unrealized_profit": "500",
            "total_margin_balance": "10500",
            "total_cross_wallet_balance": "10000",
            "available_balance": "8000",
            "max_withdraw_amount": "7500",
            "assets": [],
        }
    )

    with (
        patch("app.api.routes.sub_account.is_sub_account_configured", return_value=True),
        patch("app.api.routes.sub_account.get_sub_account_service", return_value=mock_svc),
    ):
        resp = await client.get(
            "/api/v1/sub-account/futures?email=test@test.com",
            headers=auth_headers,
        )
        assert resp.status_code == 200
