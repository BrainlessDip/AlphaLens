from fastapi import APIRouter

from app.api.routes.health import router as health_router
from app.api.routes.agent import router as agent_router
from app.api.routes.auth import router as user_auth_router
from app.api.routes.chats import router as chats_router
from app.api.routes.sub_account import router as sub_account_router
from app.api.routes.binance_status import router as binance_status_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health_router)
api_router.include_router(agent_router)
api_router.include_router(user_auth_router)
api_router.include_router(chats_router)
api_router.include_router(sub_account_router)
api_router.include_router(binance_status_router)
