import logging

from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.db.models import Base

logger = logging.getLogger(__name__)

engine = create_async_engine(get_settings().database_url, echo=False)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)

# Idempotent additive migration for pre-existing SQLite databases
# (create_all never alters existing tables).
_MISSING_COLUMNS: tuple[tuple[str, str, str], ...] = (
    ("conversations", "user_id", "VARCHAR(36)"),
    ("conversations", "title", "VARCHAR(120)"),
    ("messages", "status", "VARCHAR(20)"),
)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        if engine.dialect.name == "sqlite":
            for table, column, ddl in _MISSING_COLUMNS:
                existing = await conn.execute(text(f"PRAGMA table_info({table})"))
                names = {row[1] for row in existing.fetchall()}
                if column not in names:
                    logger.info("Migrating %s: adding column %s", table, column)
                    await conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}"))


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session
