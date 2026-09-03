from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.auth.binance_oauth import BinanceOAuthService, binance_oauth_service
from app.db.models import BinanceOAuthConnection, OAuthState, User


class TestOAuthStateManagement:
    @pytest.mark.asyncio
    async def test_create_state(self, db_session) -> None:
        user = User(username="testuser", hashed_password="hash")
        db_session.add(user)
        await db_session.commit()

        state = await binance_oauth_service.create_oauth_state(db_session, user.id)
        assert state.state
        assert state.code_verifier
        assert state.code_challenge
        assert state.user_id == user.id

    @pytest.mark.asyncio
    async def test_consume_state(self, db_session) -> None:
        user = User(username="testuser", hashed_password="hash")
        db_session.add(user)
        await db_session.commit()

        state = await binance_oauth_service.create_oauth_state(db_session, user.id)
        consumed = await binance_oauth_service.consume_oauth_state(db_session, state.state)
        assert consumed is not None
        assert consumed.consumed is True

    @pytest.mark.asyncio
    async def test_consume_state_twice_fails(self, db_session) -> None:
        user = User(username="testuser", hashed_password="hash")
        db_session.add(user)
        await db_session.commit()

        state = await binance_oauth_service.create_oauth_state(db_session, user.id)
        await binance_oauth_service.consume_oauth_state(db_session, state.state)
        result = await binance_oauth_service.consume_oauth_state(db_session, state.state)
        assert result is None

    @pytest.mark.asyncio
    async def test_consume_invalid_state_fails(self, db_session) -> None:
        result = await binance_oauth_service.consume_oauth_state(db_session, "invalid_state")
        assert result is None

    @pytest.mark.asyncio
    async def test_consume_expired_state_fails(self, db_session) -> None:
        user = User(username="testuser", hashed_password="hash")
        db_session.add(user)
        await db_session.commit()

        state = OAuthState(
            state="expired_state",
            user_id=user.id,
            code_verifier="verifier",
            code_challenge="challenge",
            created_at=datetime.now(timezone.utc) - timedelta(seconds=1200),
        )
        db_session.add(state)
        await db_session.commit()

        result = await binance_oauth_service.consume_oauth_state(db_session, "expired_state")
        assert result is None


class TestAuthorizationURL:
    def test_authorization_url_contains_required_params(self) -> None:
        url = binance_oauth_service.get_authorization_url(
            state_value="test_state",
            code_challenge="test_challenge",
        )
        assert "response_type=code" in url
        assert "client_id=" in url
        assert "code_challenge=test_challenge" in url
        assert "code_challenge_method=S256" in url
        assert "resource=" in url
        assert "state=test_state" in url
        assert "redirect_uri=" in url


class TestConnectionStatus:
    @pytest.mark.asyncio
    async def test_status_when_no_connection(self, db_session) -> None:
        status = await binance_oauth_service.get_connection_status(db_session, "nonexistent_user")
        assert status["connected"] is False
        assert status["expires_at"] is None

    @pytest.mark.asyncio
    async def test_status_when_connected(self, db_session) -> None:
        user = User(username="testuser", hashed_password="hash")
        db_session.add(user)
        await db_session.commit()

        conn = BinanceOAuthConnection(
            user_id=user.id,
            encrypted_access_token="encrypted_token",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        db_session.add(conn)
        await db_session.commit()

        status = await binance_oauth_service.get_connection_status(db_session, user.id)
        assert status["connected"] is True
        assert status["expires_at"] is not None

    @pytest.mark.asyncio
    async def test_status_when_expired_with_refresh(self, db_session) -> None:
        user = User(username="testuser", hashed_password="hash")
        db_session.add(user)
        await db_session.commit()

        conn = BinanceOAuthConnection(
            user_id=user.id,
            encrypted_access_token="encrypted_token",
            encrypted_refresh_token="encrypted_refresh",
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        db_session.add(conn)
        await db_session.commit()

        status = await binance_oauth_service.get_connection_status(db_session, user.id)
        assert status["connected"] is False
        assert status["needs_reauth"] is False

    @pytest.mark.asyncio
    async def test_status_when_expired_no_refresh(self, db_session) -> None:
        user = User(username="testuser", hashed_password="hash")
        db_session.add(user)
        await db_session.commit()

        conn = BinanceOAuthConnection(
            user_id=user.id,
            encrypted_access_token="encrypted_token",
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        db_session.add(conn)
        await db_session.commit()

        status = await binance_oauth_service.get_connection_status(db_session, user.id)
        assert status["connected"] is False
        assert status["needs_reauth"] is True


class TestDeleteConnection:
    @pytest.mark.asyncio
    async def test_delete_existing_connection(self, db_session) -> None:
        user = User(username="testuser", hashed_password="hash")
        db_session.add(user)
        await db_session.commit()

        conn = BinanceOAuthConnection(
            user_id=user.id,
            encrypted_access_token="encrypted_token",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        db_session.add(conn)
        await db_session.commit()

        result = await binance_oauth_service.delete_connection(db_session, user.id)
        assert result is True

        status = await binance_oauth_service.get_connection_status(db_session, user.id)
        assert status["connected"] is False

    @pytest.mark.asyncio
    async def test_delete_nonexistent_connection(self, db_session) -> None:
        result = await binance_oauth_service.delete_connection(db_session, "nobody")
        assert result is False


class TestMultiUserIsolation:
    @pytest.mark.asyncio
    async def test_users_have_separate_connections(self, db_session) -> None:
        user_a = User(username="user_a", hashed_password="hash_a")
        user_b = User(username="user_b", hashed_password="hash_b")
        db_session.add_all([user_a, user_b])
        await db_session.commit()

        conn_a = BinanceOAuthConnection(
            user_id=user_a.id,
            encrypted_access_token="token_a",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        conn_b = BinanceOAuthConnection(
            user_id=user_b.id,
            encrypted_access_token="token_b",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        db_session.add_all([conn_a, conn_b])
        await db_session.commit()

        status_a = await binance_oauth_service.get_connection_status(db_session, user_a.id)
        status_b = await binance_oauth_service.get_connection_status(db_session, user_b.id)
        assert status_a["connected"] is True
        assert status_b["connected"] is True

        await binance_oauth_service.delete_connection(db_session, user_a.id)

        status_a = await binance_oauth_service.get_connection_status(db_session, user_a.id)
        status_b = await binance_oauth_service.get_connection_status(db_session, user_b.id)
        assert status_a["connected"] is False
        assert status_b["connected"] is True
