import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.auth.crypto import OAuthState, create_oauth_state, generate_pkce, generate_state
from app.auth.token_store import TokenData, BinanceTokenStore


class TestStateGeneration:
    def test_generate_state_returns_urlsafe_string(self) -> None:
        state = generate_state()
        assert isinstance(state, str)
        assert len(state) > 20

    def test_generate_state_unique(self) -> None:
        states = {generate_state() for _ in range(100)}
        assert len(states) == 100


class TestPKCE:
    def test_generate_pkce_returns_verifier_and_challenge(self) -> None:
        pkce = generate_pkce()
        assert isinstance(pkce.code_verifier, str)
        assert isinstance(pkce.code_challenge, str)
        assert len(pkce.code_verifier) > 20
        assert len(pkce.code_challenge) > 20

    def test_challenge_is_s256_of_verifier(self) -> None:
        import hashlib
        import base64
        pkce = generate_pkce()
        expected = base64.urlsafe_b64encode(
            hashlib.sha256(pkce.code_verifier.encode("ascii")).digest()
        ).rstrip(b"=").decode("ascii")
        assert pkce.code_challenge == expected


class TestOAuthState:
    def test_create_oauth_state_has_all_fields(self) -> None:
        state = create_oauth_state()
        assert isinstance(state, OAuthState)
        assert state.state
        assert state.code_verifier
        assert state.code_challenge
        assert state.created_at > 0

    def test_state_not_expired_initially(self) -> None:
        state = create_oauth_state()
        assert not state.is_expired

    def test_state_expired_after_ttl(self) -> None:
        state = OAuthState(
            state="test",
            code_verifier="test",
            code_challenge="test",
            created_at=time.time() - 700,
        )
        assert state.is_expired


class TestTokenStore:
    @pytest.mark.asyncio
    async def test_save_and_get(self) -> None:
        store = BinanceTokenStore()
        token = TokenData(access_token="test_token", expires_at=time.time() + 3600)
        await store.save(token)
        retrieved = await store.get()
        assert retrieved is not None
        assert retrieved.access_token == "test_token"

    @pytest.mark.asyncio
    async def test_get_returns_none_when_empty(self) -> None:
        store = BinanceTokenStore()
        retrieved = await store.get()
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_get_returns_none_when_expired(self) -> None:
        store = BinanceTokenStore()
        token = TokenData(access_token="test", expires_at=time.time() - 1)
        await store.save(token)
        retrieved = await store.get()
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_delete(self) -> None:
        store = BinanceTokenStore()
        token = TokenData(access_token="test", expires_at=time.time() + 3600)
        await store.save(token)
        await store.delete()
        assert await store.get() is None

    def test_is_authenticated_false_when_empty(self) -> None:
        store = BinanceTokenStore()
        assert not store.is_authenticated

    def test_is_authenticated_true_when_valid_token(self) -> None:
        store = BinanceTokenStore()
        store._token = TokenData(access_token="test", expires_at=time.time() + 3600)
        assert store.is_authenticated

    def test_is_authenticated_false_when_expired(self) -> None:
        store = BinanceTokenStore()
        store._token = TokenData(access_token="test", expires_at=time.time() - 1)
        assert not store.is_authenticated


class TestAuthEndpoints:
    @pytest.mark.asyncio
    async def test_auth_status_unauthenticated(self, client) -> None:
        response = await client.get("/api/v1/binance/auth/status")
        assert response.status_code == 200
        assert response.json() == {"authenticated": False}

    @pytest.mark.asyncio
    async def test_auth_no_client_id_returns_503(self, client) -> None:
        with patch("app.api.routes.binance_auth.get_settings") as mock_settings:
            mock_settings.return_value = AsyncMock(binance_oauth_client_id="")
            response = await client.get("/api/v1/binance/auth")
            assert response.status_code == 503

    @pytest.mark.asyncio
    async def test_callback_missing_params_returns_400(self, client) -> None:
        response = await client.get("/api/v1/binance/auth/callback")
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_callback_invalid_state_returns_400(self, client) -> None:
        response = await client.get(
            "/api/v1/binance/auth/callback",
            params={"code": "test_code", "state": "invalid_state"},
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_logout(self, client) -> None:
        response = await client.post("/api/v1/binance/auth/logout")
        assert response.status_code == 200
        assert response.json() == {"authenticated": False}
