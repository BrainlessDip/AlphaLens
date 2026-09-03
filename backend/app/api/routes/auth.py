import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.user_auth import authenticate_user, create_access_token, register_user
from app.db.database import get_session

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth")


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1, max_length=100)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/register", response_model=TokenResponse, summary="Register a new user")
async def register(
    request: RegisterRequest,
    session: AsyncSession = Depends(get_session),
) -> TokenResponse:
    try:
        user = await register_user(session, request.username, request.password)
    except ValueError as e:
        raise HTTPException(status_code=409, detail={"error": {"code": "USER_EXISTS", "message": str(e)}})

    token = create_access_token(user.id)
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse, summary="Login")
async def login(
    request: LoginRequest,
    session: AsyncSession = Depends(get_session),
) -> TokenResponse:
    user = await authenticate_user(session, request.username, request.password)
    if user is None:
        raise HTTPException(status_code=401, detail={"error": {"code": "INVALID_CREDENTIALS", "message": "Invalid username or password"}})

    token = create_access_token(user.id)
    return TokenResponse(access_token=token)
