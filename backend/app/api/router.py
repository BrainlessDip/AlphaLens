from fastapi import APIRouter

from app.api.routes.health import router as health_router
from app.api.routes.agent import router as agent_router
from app.api.routes.binance_auth import router as binance_auth_router
from app.api.routes.auth import router as user_auth_router
from app.api.routes.metadata import router as metadata_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health_router)
api_router.include_router(agent_router)
api_router.include_router(binance_auth_router)
api_router.include_router(user_auth_router)

# Metadata endpoint is at root, not under /api/v1
# Included separately in main.py
