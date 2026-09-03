import json

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.core.config import get_settings

router = APIRouter()


@router.get("/.well-known/oauth-client-metadata.json", summary="OAuth Client ID Metadata Document")
async def client_metadata() -> JSONResponse:
    settings = get_settings()
    metadata = {
        "client_name": "Binance Agent OS",
        "grant_types": [
            "authorization_code",
        ],
        "response_types": [
            "code",
        ],
        "token_endpoint_auth_method": "none",
        "application_type": "native",
        "client_id": settings.binance_oauth_client_metadata_url,
        "client_uri": settings.frontend_url,
        "redirect_uris": [
            settings.binance_oauth_redirect_uri,
        ],
    }
    return JSONResponse(content=metadata)
