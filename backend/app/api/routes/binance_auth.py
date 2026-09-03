import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.binance_oauth import binance_oauth_service
from app.auth.user_auth import get_current_user
from app.core.config import get_settings
from app.db.database import get_session
from app.db.models import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/binance")


async def _get_user(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> User:
    """FastAPI dependency: extract current user from Authorization header."""
    auth_header = request.headers.get("Authorization")
    return await get_current_user(authorization=auth_header, session=session)


@router.get("/auth", summary="Start Binance OAuth flow")
async def start_auth(
    user: User = Depends(_get_user),
    session: AsyncSession = Depends(get_session),
) -> RedirectResponse:
    settings = get_settings()

    if not settings.binance_oauth_client_metadata_url:
        raise HTTPException(
            status_code=503,
            detail={
                "error": {
                    "code": "BINANCE_OAUTH_NOT_CONFIGURED",
                    "message": "BINANCE_OAUTH_CLIENT_METADATA_URL is not configured.",
                }
            },
        )

    await binance_oauth_service.cleanup_expired_states(session)

    oauth_state = await binance_oauth_service.create_oauth_state(session, user.id)

    auth_url = binance_oauth_service.get_authorization_url(
        state_value=oauth_state.state,
        code_challenge=oauth_state.code_challenge,
    )

    return RedirectResponse(url=auth_url)


@router.get("/auth/callback", summary="Handle OAuth callback")
async def auth_callback(
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
    error_description: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
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

    oauth_state = await binance_oauth_service.consume_oauth_state(session, state)
    if oauth_state is None:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "OAUTH_INVALID_STATE",
                    "message": "Invalid, expired, or already-used OAuth state.",
                }
            },
        )

    conn = await binance_oauth_service.exchange_code(
        session=session,
        user_id=oauth_state.user_id,
        code=code,
        code_verifier=oauth_state.code_verifier,
    )

    if conn is None:
        raise HTTPException(
            status_code=502,
            detail={
                "error": {
                    "code": "OAUTH_TOKEN_EXCHANGE_FAILED",
                    "message": "Failed to exchange authorization code for token.",
                }
            },
        )

    return {"authenticated": True}


@router.get("/auth/status", summary="Check Binance auth status")
async def auth_status(
    user: User = Depends(_get_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    status = await binance_oauth_service.get_connection_status(session, user.id)
    return status


@router.post("/auth/logout", summary="Logout from Binance")
async def logout(
    user: User = Depends(_get_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    await binance_oauth_service.delete_connection(session, user.id)
    return {"authenticated": False}
