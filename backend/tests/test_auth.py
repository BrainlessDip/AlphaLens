import pytest

from app.auth.user_auth import (
    authenticate_user,
    create_access_token,
    decode_access_token,
    hash_password,
    register_user,
    verify_password,
)


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
