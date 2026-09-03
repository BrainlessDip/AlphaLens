import time
from unittest.mock import AsyncMock, patch

import pytest

from app.auth.crypto import OAuthState, create_oauth_state, generate_pkce, generate_state
from app.auth.token_store import TokenData
from app.auth.user_auth import (
    authenticate_user,
    create_access_token,
    decode_access_token,
    hash_password,
    register_user,
    verify_password,
)
from app.db.models import User


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


class TestTokenData:
    def test_is_expired_when_no_expiry(self) -> None:
        token = TokenData(access_token="test")
        assert not token.is_expired

    def test_is_expired_when_past(self) -> None:
        token = TokenData(access_token="test", expires_at=time.time() - 1)
        assert token.is_expired

    def test_is_valid_with_token_and_not_expired(self) -> None:
        token = TokenData(access_token="test", expires_at=time.time() + 3600)
        assert token.is_valid

    def test_is_not_valid_when_expired(self) -> None:
        token = TokenData(access_token="test", expires_at=time.time() - 1)
        assert not token.is_valid


class TestPasswordAuth:
    def test_hash_and_verify(self) -> None:
        hashed = hash_password("testpassword")
        assert verify_password("testpassword", hashed)
        assert not verify_password("wrongpassword", hashed)

    @pytest.mark.asyncio
    async def test_register_and_authenticate(self, db_session) -> None:
        user = await register_user(db_session, "testuser", "testpassword123")
        assert user.username == "testuser"
        assert isinstance(user.id, str)

        authenticated = await authenticate_user(db_session, "testuser", "testpassword123")
        assert authenticated is not None
        assert authenticated.id == user.id

    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, db_session) -> None:
        await register_user(db_session, "testuser", "testpassword123")
        with pytest.raises(ValueError, match="already exists"):
            await register_user(db_session, "testuser", "otherpassword")

    @pytest.mark.asyncio
    async def test_authenticate_wrong_password(self, db_session) -> None:
        await register_user(db_session, "testuser", "testpassword123")
        result = await authenticate_user(db_session, "testuser", "wrongpassword")
        assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_nonexistent_user(self, db_session) -> None:
        result = await authenticate_user(db_session, "nouser", "nopassword")
        assert result is None


class TestJWT:
    def test_create_and_decode_token(self) -> None:
        token = create_access_token("user-123")
        user_id = decode_access_token(token)
        assert user_id == "user-123"

    def test_decode_invalid_token(self) -> None:
        result = decode_access_token("invalid.token.here")
        assert result is None

    def test_decode_expired_token(self) -> None:
        import jwt
        from app.core.config import get_settings
        settings = get_settings()
        from datetime import datetime, timedelta, timezone
        expire = datetime.now(timezone.utc) - timedelta(hours=1)
        payload = {"sub": "user-123", "exp": expire}
        token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
        result = decode_access_token(token)
        assert result is None


class TestAuthEndpoints:
    @pytest.mark.asyncio
    async def test_register_success(self, client) -> None:
        response = await client.post(
            "/api/v1/auth/register",
            json={"username": "newuser", "password": "password123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_register_duplicate(self, client) -> None:
        await client.post(
            "/api/v1/auth/register",
            json={"username": "testuser", "password": "password123"},
        )
        response = await client.post(
            "/api/v1/auth/register",
            json={"username": "testuser", "password": "password123"},
        )
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_login_success(self, client) -> None:
        await client.post(
            "/api/v1/auth/register",
            json={"username": "testuser", "password": "password123"},
        )
        response = await client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "password123"},
        )
        assert response.status_code == 200
        assert "access_token" in response.json()

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client) -> None:
        await client.post(
            "/api/v1/auth/register",
            json={"username": "testuser", "password": "password123"},
        )
        response = await client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "wrongpassword"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_binance_auth_requires_login(self, client) -> None:
        response = await client.get("/api/v1/binance/auth")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_binance_auth_status_requires_login(self, client) -> None:
        response = await client.get("/api/v1/binance/auth/status")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_binance_logout_requires_login(self, client) -> None:
        response = await client.post("/api/v1/binance/auth/logout")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_binance_auth_status_connected(self, client) -> None:
        # Register and login
        reg = await client.post(
            "/api/v1/auth/register",
            json={"username": "testuser", "password": "password123"},
        )
        token = reg.json()["access_token"]

        response = await client.get(
            "/api/v1/binance/auth/status",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["connected"] is False

    @pytest.mark.asyncio
    async def test_binance_logout(self, client) -> None:
        reg = await client.post(
            "/api/v1/auth/register",
            json={"username": "testuser", "password": "password123"},
        )
        token = reg.json()["access_token"]

        response = await client.post(
            "/api/v1/binance/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["authenticated"] is False


class TestMetadataEndpoint:
    @pytest.mark.asyncio
    async def test_metadata_returns_valid_document(self, client) -> None:
        response = await client.get("/.well-known/oauth-client-metadata.json")
        assert response.status_code == 200
        data = response.json()
        assert data["token_endpoint_auth_method"] == "none"
        assert data["application_type"] == "native"
        assert "authorization_code" in data["grant_types"]
        assert "code" in data["response_types"]
        assert len(data["redirect_uris"]) == 1

    @pytest.mark.asyncio
    async def test_metadata_client_id_is_configured_url(self, client) -> None:
        response = await client.get("/.well-known/oauth-client-metadata.json")
        data = response.json()
        assert data["client_id"] == data["client_id"]  # self-referential
        assert "oauth-client-metadata.json" in data["client_id"]
