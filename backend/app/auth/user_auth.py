import logging
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.database import get_session
from app.db.models import User

logger = logging.getLogger(__name__)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def create_access_token(user_id: str) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": user_id, "exp": expire}
    return jwt.encode(
        payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )


def decode_access_token(token: str) -> str | None:
    """Decode JWT and return user_id, or None if invalid."""
    settings = get_settings()
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        return payload.get("sub")
    except jwt.PyJWTError:
        return None


async def get_current_user(
    authorization: str | None = None,
    session: AsyncSession | None = None,
) -> User:
    """Extract and validate user from Authorization header.

    This is the core auth dependency. Routes use it via the
    ``get_current_user_dep`` FastAPI dependency which parses the header.
    """
    if not authorization or not authorization.startswith("Bearer "):
        from app.core.exceptions import AuthRequiredError

        raise AuthRequiredError()

    token = authorization[7:]
    user_id = decode_access_token(token)
    if user_id is None:
        from app.core.exceptions import AuthRequiredError

        raise AuthRequiredError()

    if session is None:
        from app.db.database import async_session_factory

        async with async_session_factory() as session:
            result = await session.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
    else:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

    if user is None:
        from app.core.exceptions import AuthRequiredError

        raise AuthRequiredError()

    return user


async def current_user_dep(
    authorization: str | None = Header(default=None),
    session: AsyncSession = Depends(get_session),
) -> User:
    """FastAPI dependency: current authenticated user (401 otherwise)."""
    return await get_current_user(authorization, session)


async def register_user(session: AsyncSession, username: str, password: str) -> User:
    """Register a new user. Raises ValueError if username exists."""
    existing = await session.execute(select(User).where(User.username == username))
    if existing.scalar_one_or_none() is not None:
        raise ValueError("Username already exists")

    user = User(username=username, hashed_password=hash_password(password))
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def authenticate_user(
    session: AsyncSession, username: str, password: str
) -> User | None:
    """Authenticate user by username/password. Returns User or None."""
    result = await session.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(password, user.hashed_password):
        return None
    return user
