import logging
from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse

from app.auth.crypto import create_oauth_state, OAuthState
from app.auth.oauth import binance_oauth
from app.auth.token_store import token_store
from app.core.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/binance")

# In-memory state store
_oauth_states: dict[str, OAuthState] = {}


@router.get("/auth", summary="Start Binance OAuth flow")
async def start_auth() -> RedirectResponse:
    settings = get_settings()

    if not settings.binance_oauth_client_id:
        raise HTTPException(
            status_code=503,
            detail={
                "error": {
                    "code": "BINANCE_OAUTH_NOT_CONFIGURED",
                    "message": "BINANCE_OAUTH_CLIENT_ID is not configured. Register a Binance OAuth app first.",
                }
            },
        )

    # Cleanup expired states
    expired = [k for k, v in _oauth_states.items() if v.is_expired]
    for k in expired:
        del _oauth_states[k]

    oauth_state = create_oauth_state()
    _oauth_states[oauth_state.state] = oauth_state

    auth_url = await binance_oauth.get_authorization_url(
        state=oauth_state.state,
        code_challenge=oauth_state.code_challenge,
        redirect_uri=settings.binance_oauth_redirect_uri,
        scopes=settings.binance_oauth_scopes or None,
    )

    return RedirectResponse(url=auth_url)


@router.get("/auth/callback", summary="Handle OAuth callback")
async def auth_callback(
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
    error_description: str | None = Query(default=None),
) -> dict:
    if error:
        logger.warning("OAuth error: %s - %s", error, error_description)
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "OAUTH_DENIAL",
                    "message": f"Authorization denied: {error_description or error}",
                }
            },
        )

    if not code or not state:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "OAUTH_INVALID_CALLBACK",
                    "message": "Missing authorization code or state parameter.",
                }
            },
        )

    stored_state = _oauth_states.pop(state, None)
    if stored_state is None:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "OAUTH_INVALID_STATE",
                    "message": "Invalid or expired OAuth state. Please try again.",
                }
            },
        )

    if stored_state.is_expired:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "OAUTH_STATE_EXPIRED",
                    "message": "OAuth state expired. Please try again.",
                }
            },
        )

    if stored_state.state != state:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "OAUTH_STATE_MISMATCH",
                    "message": "OAuth state mismatch. Possible CSRF attack.",
                }
            },
        )

    settings = get_settings()

    try:
        token = await binance_oauth.exchange_code(
            code=code,
            code_verifier=stored_state.code_verifier,
            redirect_uri=settings.binance_oauth_redirect_uri,
        )
    except Exception as e:
        logger.error("Token exchange failed: %s", e)
        raise HTTPException(
            status_code=502,
            detail={
                "error": {
                    "code": "OAUTH_TOKEN_EXCHANGE_FAILED",
                    "message": "Failed to exchange authorization code for token.",
                }
            },
        )

    return {"authenticated": True, "token_type": token.token_type, "scope": token.scope}


@router.get("/auth/status", summary="Check Binance auth status")
async def auth_status() -> dict:
    return {"authenticated": token_store.is_authenticated}


@router.post("/auth/logout", summary="Logout from Binance")
async def logout() -> dict:
    await token_store.delete()
    return {"authenticated": False}
