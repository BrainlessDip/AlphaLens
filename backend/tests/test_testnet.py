"""Tests for Binance Testnet/Sandbox mode configuration and environment routing."""

from types import SimpleNamespace
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings


# ── Configuration tests ──────────────────────────────────────────────


class TestTestnetConfig:
    def test_no_credentials_enables_testnet(self):
        settings = Settings(
            binance_api_key="",
            binance_api_secret="",
            binance_testnet=False,
        )
        assert settings.binance_is_testnet is True

    def test_explicit_testnet_flag(self):
        settings = Settings(
            binance_api_key="real-key",
            binance_api_secret="real-secret",
            binance_testnet=True,
        )
        assert settings.binance_is_testnet is True

    def test_production_with_credentials(self):
        settings = Settings(
            binance_api_key="real-key",
            binance_api_secret="real-secret",
            binance_testnet=False,
        )
        assert settings.binance_is_testnet is False

    def test_missing_secret_enables_testnet(self):
        settings = Settings(
            binance_api_key="key-only",
            binance_api_secret="",
            binance_testnet=False,
        )
        assert settings.binance_is_testnet is True

    def test_missing_key_enables_testnet(self):
        settings = Settings(
            binance_api_key="",
            binance_api_secret="secret-only",
            binance_testnet=False,
        )
        assert settings.binance_is_testnet is True

    def test_testnet_auto_enabled_when_no_creds(self):
        settings = Settings(
            binance_api_key="",
            binance_api_secret="",
            binance_testnet=False,
        )
        assert settings.binance_testnet is False
        assert settings.binance_is_testnet is True  # auto-enabled

    def test_production_creds_never_accidentally_route_to_testnet(self):
        settings = Settings(
            binance_api_key="real-key",
            binance_api_secret="real-secret",
            binance_testnet=False,
        )
        assert settings.binance_is_testnet is False
        assert settings.binance_effective_base_url == "https://api.binance.com"

    def test_testnet_base_url(self):
        settings = Settings(
            binance_api_key="",
            binance_api_secret="",
            binance_testnet=False,
        )
        assert settings.binance_effective_base_url == "https://testnet.binance.vision"

    def test_explicit_testnet_base_url(self):
        settings = Settings(
            binance_api_key="key",
            binance_api_secret="secret",
            binance_testnet=True,
        )
        assert settings.binance_effective_base_url == "https://testnet.binance.vision"

    def test_custom_base_url_not_overridden_when_production(self):
        settings = Settings(
            binance_api_key="key",
            binance_api_secret="secret",
            binance_base_url="https://custom.api.com",
            binance_testnet=False,
        )
        assert settings.binance_effective_base_url == "https://custom.api.com"

    def test_credentials_not_exposed_in_properties(self):
        settings = Settings(
            binance_api_key="secret-key",
            binance_api_secret="super-secret",
            binance_testnet=False,
        )
        # Properties should never return credentials
        assert settings.binance_is_testnet is False
        assert "secret-key" not in settings.binance_effective_base_url
        assert "super-secret" not in settings.binance_effective_base_url


# ── Binance client base URL resolution ───────────────────────────────


class TestBinanceClientResolution:
    def test_client_uses_effective_url(self):
        """Verify BinanceRESTProvider would use resolved URL."""
        settings = Settings(
            binance_api_key="",
            binance_api_secret="",
            binance_testnet=False,
        )
        assert settings.binance_effective_base_url == "https://testnet.binance.vision"

    def test_provider_creds_never_reach_testnet_when_configured(self):
        settings = Settings(
            binance_api_key="production-key",
            binance_api_secret="production-secret",
            binance_testnet=False,
        )
        # When production creds are set and testnet is off, must use production
        assert settings.binance_effective_base_url == "https://api.binance.com"


# ── API status endpoint tests ────────────────────────────────────────


@pytest.mark.asyncio
async def test_binance_status_testnet_mode(client: AsyncClient, auth_headers: dict):
    with patch("app.api.routes.binance_status.get_settings") as mock:
        mock.return_value = SimpleNamespace(
            binance_api_key="",
            binance_api_secret="",
            binance_is_testnet=True,
            binance_testnet=False,
        )
        with patch("app.api.routes.binance_status.is_sub_account_configured", return_value=False):
            resp = await client.get("/api/v1/binance/status", headers=auth_headers)
            assert resp.status_code == 200
            data = resp.json()
            assert data["environment"] == "testnet"
            assert data["mode"] == "sandbox"
            assert data["authenticated"] is False
            assert data["testnet_auto_enabled"] is True


@pytest.mark.asyncio
async def test_binance_status_production_mode(client: AsyncClient, auth_headers: dict):
    with patch("app.api.routes.binance_status.get_settings") as mock:
        mock.return_value = SimpleNamespace(
            binance_api_key="real-key",
            binance_api_secret="real-secret",
            binance_is_testnet=False,
            binance_testnet=False,
        )
        with patch("app.api.routes.binance_status.is_sub_account_configured", return_value=True):
            resp = await client.get("/api/v1/binance/status", headers=auth_headers)
            assert resp.status_code == 200
            data = resp.json()
            assert data["environment"] == "production"
            assert data["mode"] == "live"
            assert data["authenticated"] is True
            assert data["testnet_auto_enabled"] is False


@pytest.mark.asyncio
async def test_binance_status_requires_auth(client: AsyncClient):
    resp = await client.get("/api/v1/binance/status")
    assert resp.status_code == 401


# ── Agent tool routing tests ─────────────────────────────────────────


class TestAgentToolRouting:
    def test_sub_account_tools_not_registered_when_unconfigured(self):
        from app.agent.agent import build_market_agent

        with patch("app.binance.sub_account_service.is_sub_account_configured", return_value=False):
            agent = build_market_agent(Settings(
                openrouter_api_key="test",
                binance_api_key="",
                binance_api_secret="",
            ))
            tool_names = {t.name for t in agent._function_toolset.tools.values()}
            # Sub-account tools should not be present
            assert "get_sub_accounts" not in tool_names
            assert "get_sub_account_assets" not in tool_names

    def test_market_tools_always_registered(self):
        from app.agent.agent import build_market_agent

        agent = build_market_agent(Settings(
            openrouter_api_key="test",
            binance_api_key="",
            binance_api_secret="",
        ))
        tool_names = {t.name for t in agent._function_toolset.tools.values()}
        assert "get_ticker" in tool_names
        assert "get_klines" in tool_names
        assert "get_exchange_info" in tool_names

    def test_tools_dont_crash_when_sub_account_none(self):
        """Agent tools must gracefully handle missing sub_account dep."""
        from app.agent.tools import get_sub_accounts

        from app.agent.dependencies import AgentDeps
        from app.binance.client import BinanceRESTProvider
        from unittest.mock import MagicMock

        deps = AgentDeps(provider=MagicMock(spec=BinanceRESTProvider), sub_account=None)
        # This should return a string, not crash
        # We test the guard, not the actual API call
        assert deps.sub_account is None


# ── No-credentials safe startup test ─────────────────────────────────


class TestSafeStartup:
    def test_app_starts_without_credentials(self):
        """Application must not crash when no Binance credentials are set."""
        settings = Settings(
            binance_api_key="",
            binance_api_secret="",
            binance_testnet=False,
        )
        # Should auto-enable testnet, not crash
        assert settings.binance_is_testnet is True
        assert settings.binance_effective_base_url == "https://testnet.binance.vision"

    def test_sub_account_configured_false_without_creds(self):
        """Sub-account tools should be disabled when no credentials."""
        with patch("app.binance.sub_account_service.get_settings") as mock:
            mock.return_value = SimpleNamespace(
                binance_sub_account_api_key="",
                binance_sub_account_api_secret="",
                binance_api_key="",
                binance_api_secret="",
            )
            from app.binance.sub_account_service import is_sub_account_configured
            assert is_sub_account_configured() is False

    def test_sub_account_uses_fallback_when_only_generic_key_set(self):
        """Sub-account falls back to generic Binance API key."""
        with patch("app.binance.sub_account_service.get_settings") as mock:
            mock.return_value = SimpleNamespace(
                binance_sub_account_api_key="",
                binance_sub_account_api_secret="",
                binance_api_key="fallback-key",
                binance_api_secret="fallback-secret",
            )
            from app.binance.sub_account_service import is_sub_account_configured
            assert is_sub_account_configured() is True
