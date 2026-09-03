from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.exceptions import AppException, app_exception_handler
from app.core.logging import setup_logging
from app.db.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    setup_logging()
    await init_db()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Binance Agent OS Backend",
        description="AI-powered Binance Market Intelligence Agent",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_exception_handler(AppException, app_exception_handler)  # type: ignore[arg-type]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_url],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from app.api.router import api_router
    from app.api.routes.metadata import router as metadata_router

    app.include_router(api_router)
    app.include_router(metadata_router)

    return app


app = create_app()
