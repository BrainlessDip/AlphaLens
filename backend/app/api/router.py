from fastapi import APIRouter

from app.api.routes.health import router as health_router
from app.api.routes.agent import router as agent_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health_router)
api_router.include_router(agent_router)
