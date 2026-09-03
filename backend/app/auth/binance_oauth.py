import logging
import time
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.models import BinanceOAuthConnection, OAuthState, User
from app.auth.token_encryption import encrypt_token, decrypt_token
from app.auth.crypto import generate_state, generate_pkce

logger = logging.getLogger(__name__)

STATE_TTL_SECONDS = 600


class BinanceOAuthService:
    """Multi-user Binance OAuth service backed by the database."""

    def __init__(self) -> None:
        self._client = httpx.AsyncClient(timeout=30.0)

    # ── State management ──────────────────────────────────────────────

    async def create_oauth_state(self, session: AsyncSession, user_id: str) -> OAuthState:
        """Create a new OAuth state tied to a user."""
        state_value = generate_state()
        pkce = generate_pkce()

        oauth_state = OAuthState(
            state=state_value,
            user_id=user_id,
            code_verifier=pkce.code_verifier,
            code_challenge=pkce.code_challenge,
        )
        session.add(oauth_state)
        await session.commit()
        return oauth_state

    async def consume_oauth_state(self, session: AsyncSession, state_value: str) -> OAuthState | None:
        """Retrieve and consume an OAuth state. Returns None if invalid/expired/already used."""
        result = await session.execute(
            select(OAuthState).where(OAuthState.state == state_value)
        )
        oauth_state = result.scalar_one_or_none()
        if oauth_state is None:
            return None
        if oauth_state.consumed:
            return None

        settings = get_settings()
        created_utc = oauth_state.created_at.replace(tzinfo=timezone.utc) if oauth_state.created_at.tzinfo is None else oauth_state.created_at
        if (datetime.now(timezone.utc) - created_utc).total_seconds() > settings.state_ttl_seconds:
            return None

        oauth_state.consumed = True
        await session.commit()
        return oauth_state

    async def cleanup_expired_states(self, session: AsyncSession) -> int:
        """Delete expired states. Returns count deleted."""
        settings = get_settings()
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=settings.state_ttl_seconds)
        result = await session.execute(select(OAuthState).where(OAuthState.created_at < cutoff))
        states = result.scalars().all()
        for s in states:
            await session.delete(s)
        await session.commit()
        return len(states)

    # ── Authorization URL ─────────────────────────────────────────────

    def get_authorization_url(
        self,
        state_value: str,
        code_challenge: str,
    ) -> str:
        settings = get_settings()
        from urllib.parse import urlencode
        params = {
            "response_type": "code",
            "client_id": settings.binance_oauth_client_metadata_url,
            "redirect_uri": settings.binance_oauth_redirect_uri,
            "state": state_value,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "resource": settings.binance_oauth_mcp_resource,
        }
        return f"{settings.binance_oauth_authorization_endpoint}?{urlencode(params)}"

    # ── Token exchange ────────────────────────────────────────────────

    async def exchange_code(
        self,
        session: AsyncSession,
        user_id: str,
        code: str,
        code_verifier: str,
    ) -> BinanceOAuthConnection | None:
        """Exchange authorization code for tokens. Stores connection in DB."""
        settings = get_settings()
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.binance_oauth_redirect_uri,
            "code_verifier": code_verifier,
            "client_id": settings.binance_oauth_client_metadata_url,
        }

        try:
            resp = await self._client.post(settings.binance_oauth_token_endpoint, data=data)
            if resp.status_code != 200:
                logger.error("Token exchange failed: %s %s", resp.status_code, resp.text)
                return None

            token_data = resp.json()
            expires_in = token_data.get("expires_in", 3600)
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

            # Upsert connection (one per user)
            result = await session.execute(
                select(BinanceOAuthConnection).where(BinanceOAuthConnection.user_id == user_id)
            )
            conn = result.scalar_one_or_none()
            if conn is None:
                conn = BinanceOAuthConnection(user_id=user_id)
                session.add(conn)

            conn.encrypted_access_token = encrypt_token(token_data["access_token"])
            refresh = token_data.get("refresh_token")
            if refresh:
                conn.encrypted_refresh_token = encrypt_token(refresh)
            conn.expires_at = expires_at
            await session.commit()
            return conn

        except Exception as e:
            logger.error("Token exchange error: %s", e)
            return None

    # ── Token refresh ─────────────────────────────────────────────────

    async def refresh_token(
        self,
        session: AsyncSession,
        connection: BinanceOAuthConnection,
    ) -> bool:
        """Refresh the access token. Returns True on success."""
        settings = get_settings()
        refresh_token = decrypt_token(connection.encrypted_refresh_token)
        if not refresh_token:
            return False

        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": settings.binance_oauth_client_metadata_url,
        }

        try:
            resp = await self._client.post(settings.binance_oauth_token_endpoint, data=data)
            if resp.status_code != 200:
                logger.error("Token refresh failed: %s", resp.status_code)
                return False

            token_data = resp.json()
            expires_in = token_data.get("expires_in", 3600)

            connection.encrypted_access_token = encrypt_token(token_data["access_token"])
            new_refresh = token_data.get("refresh_token")
            if new_refresh:
                connection.encrypted_refresh_token = encrypt_token(new_refresh)
            connection.expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
            await session.commit()
            return True

        except Exception as e:
            logger.error("Token refresh error: %s", e)
            return False

    # ── Get valid token ───────────────────────────────────────────────

    async def get_valid_token(
        self,
        session: AsyncSession,
        user_id: str,
    ) -> str | None:
        """Get a valid access token for the user, refreshing if needed. Returns token string or None."""
        result = await session.execute(
            select(BinanceOAuthConnection).where(BinanceOAuthConnection.user_id == user_id)
        )
        conn = result.scalar_one_or_none()
        if conn is None:
            return None

        now_utc = datetime.now(timezone.utc)
        expires_at = conn.expires_at.replace(tzinfo=timezone.utc) if conn.expires_at.tzinfo is None else conn.expires_at

        # If expired and has refresh token, try refresh
        if now_utc >= expires_at:
            if conn.encrypted_refresh_token:
                refreshed = await self.refresh_token(session, conn)
                if not refreshed:
                    return None
                # Re-read after refresh
                await session.refresh(conn)
            else:
                return None

        return decrypt_token(conn.encrypted_access_token)

    # ── Connection status ─────────────────────────────────────────────

    async def get_connection_status(
        self,
        session: AsyncSession,
        user_id: str,
    ) -> dict:
        """Get safe connection status for the user."""
        result = await session.execute(
            select(BinanceOAuthConnection).where(BinanceOAuthConnection.user_id == user_id)
        )
        conn = result.scalar_one_or_none()
        if conn is None:
            return {"connected": False, "expires_at": None, "needs_reauth": False}

        now_utc = datetime.now(timezone.utc)
        expires_at = conn.expires_at.replace(tzinfo=timezone.utc) if conn.expires_at.tzinfo is None else conn.expires_at
        is_expired = now_utc >= expires_at
        needs_reauth = is_expired and not conn.encrypted_refresh_token

        return {
            "connected": not is_expired,
            "expires_at": conn.expires_at.isoformat(),
            "needs_reauth": needs_reauth,
        }

    # ── Delete connection ─────────────────────────────────────────────

    async def delete_connection(self, session: AsyncSession, user_id: str) -> bool:
        """Delete the user's Binance connection. Returns True if deleted."""
        result = await session.execute(
            select(BinanceOAuthConnection).where(BinanceOAuthConnection.user_id == user_id)
        )
        conn = result.scalar_one_or_none()
        if conn is None:
            return False
        await session.delete(conn)
        await session.commit()
        return True

    # ── Cleanup ───────────────────────────────────────────────────────

    async def close(self) -> None:
        await self._client.aclose()


binance_oauth_service = BinanceOAuthService()
