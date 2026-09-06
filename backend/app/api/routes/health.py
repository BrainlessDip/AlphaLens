import logging

import httpx
from fastapi import APIRouter
from app.core.config import get_settings
from app.schemas.common import HealthResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", response_model=HealthResponse, summary="Health check")
async def health_check() -> HealthResponse:
    settings = get_settings()
    binance_status = "unknown"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.binance_base_url}/api/v3/ping")
            binance_status = "operational" if resp.status_code == 200 else "degraded"
    except Exception as e:
        logger.warning("Binance ping failed: %s", type(e).__name__)
        binance_status = "unavailable"
    return HealthResponse(
        status="ok",
        model=settings.openrouter_model,
        binance_status=binance_status,
    )
