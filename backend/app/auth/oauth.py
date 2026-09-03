import logging
import time

import httpx

from app.auth.token_store import TokenData, token_store
from app.core.config import get_settings

logger = logging.getLogger(__name__)


class BinanceOAuth:
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(timeout=30.0)

    async def get_authorization_url(
        self,
        state: str,
        code_challenge: str,
        redirect_uri: str,
        scopes: str | None = None,
    ) -> str:
        settings = get_settings()
        params = {
            "response_type": "code",
            "client_id": settings.binance_oauth_client_id,
            "redirect_uri": redirect_uri,
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
        if scopes:
            params["scope"] = scopes

        return f"{settings.binance_oauth_authorization_endpoint}?{httpx.URL(params).__query__}"

    async def exchange_code(
        self,
        code: str,
        code_verifier: str,
        redirect_uri: str,
    ) -> TokenData:
        settings = get_settings()
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "code_verifier": code_verifier,
            "client_id": settings.binance_oauth_client_id,
        }

        resp = await self._client.post(settings.binance_oauth_token_endpoint, data=data)
        if resp.status_code != 200:
            logger.error("Token exchange failed: %s %s", resp.status_code, resp.text)
            raise ValueError(f"Token exchange failed: {resp.status_code}")

        token_data = resp.json()
        expires_at = time.time() + token_data.get("expires_in", 3600)

        token = TokenData(
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token"),
            expires_at=expires_at,
            token_type=token_data.get("token_type", "Bearer"),
            scope=token_data.get("scope"),
        )

        await token_store.save(token)
        return token

    async def refresh_access_token(self, refresh_token: str) -> TokenData | None:
        settings = get_settings()
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": settings.binance_oauth_client_id,
        }

        try:
            resp = await self._client.post(settings.binance_oauth_token_endpoint, data=data)
            if resp.status_code != 200:
                logger.error("Token refresh failed: %s", resp.status_code)
                await token_store.delete()
                return None

            token_data = resp.json()
            expires_at = time.time() + token_data.get("expires_in", 3600)

            token = TokenData(
                access_token=token_data["access_token"],
                refresh_token=token_data.get("refresh_token", refresh_token),
                expires_at=expires_at,
                token_type=token_data.get("token_type", "Bearer"),
                scope=token_data.get("scope"),
            )

            await token_store.save(token)
            return token
        except Exception as e:
            logger.error("Token refresh error: %s", e)
            await token_store.delete()
            return None

    async def close(self) -> None:
        await self._client.aclose()


binance_oauth = BinanceOAuth()
