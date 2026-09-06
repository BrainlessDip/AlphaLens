import hashlib
import hmac
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.user_auth import current_user_dep
from app.core.config import get_settings
from app.db.database import get_session
from app.db.models import Conversation, Message, User
from app.schemas.chat import (
    ChatDetailResponse,
    ChatListResponse,
    ChatMessageItem,
    ChatSummary,
    CreateChatResponse,
    RenameChatRequest,
    ShareResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chats")


def _iso(dt) -> str:
    return dt.isoformat()


async def _get_owned_conversation(session: AsyncSession, user_id: str, chat_id: str) -> Conversation:
    result = await session.execute(
        select(Conversation).where(
            Conversation.id == chat_id,
            Conversation.user_id == user_id,
        )
    )
    conversation = result.scalar_one_or_none()
    if conversation is None:
        raise HTTPException(status_code=404, detail={"error": {"code": "CHAT_NOT_FOUND", "message": "Chat not found."}})
    return conversation


@router.get("", response_model=ChatListResponse, summary="List chats")
async def list_chats(
    search: str | None = Query(default=None, max_length=100),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(current_user_dep),
    session: AsyncSession = Depends(get_session),
) -> ChatListResponse:
    filters = [Conversation.user_id == user.id]
    if search:
        like = f"%{search}%"
        filters.append(
            or_(
                Conversation.title.ilike(like),
                Conversation.messages.any(Message.content.ilike(like)),
            )
        )

    total = (
        await session.execute(
            select(func.count()).select_from(Conversation).where(*filters)
        )
    ).scalar_one()

    rows = (
        await session.execute(
            select(Conversation)
            .where(*filters)
            .order_by(Conversation.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
    ).scalars().all()

    items = [
        ChatSummary(
            id=c.id,
            title=c.title,
            created_at=_iso(c.created_at),
            updated_at=_iso(c.updated_at),
            message_count=len(c.messages),
        )
        for c in rows
    ]
    return ChatListResponse(items=items, total=total)


@router.post("", response_model=CreateChatResponse, status_code=201, summary="Create chat")
async def create_chat(
    user: User = Depends(current_user_dep),
    session: AsyncSession = Depends(get_session),
) -> CreateChatResponse:
    conversation = Conversation(user_id=user.id)
    session.add(conversation)
    await session.commit()
    await session.refresh(conversation)
    return CreateChatResponse(id=conversation.id, title=conversation.title)


@router.get("/{chat_id}", response_model=ChatDetailResponse, summary="Get chat with messages")
async def get_chat(
    chat_id: str,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(current_user_dep),
    session: AsyncSession = Depends(get_session),
) -> ChatDetailResponse:
    conversation = await _get_owned_conversation(session, user.id, chat_id)
    msgs = (
        await session.execute(
            select(Message)
            .where(Message.conversation_id == chat_id)
            .order_by(Message.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
    ).scalars().all()
    return ChatDetailResponse(
        id=conversation.id,
        title=conversation.title,
        created_at=_iso(conversation.created_at),
        updated_at=_iso(conversation.updated_at),
        messages=[
            ChatMessageItem(
                id=m.id,
                chat_id=m.conversation_id,
                role=m.role,
                content=m.content,
                status=m.status,
                created_at=_iso(m.created_at),
            )
            for m in msgs
        ],
    )


@router.patch("/{chat_id}", response_model=ChatSummary, summary="Rename chat")
async def rename_chat(
    chat_id: str,
    request: RenameChatRequest,
    user: User = Depends(current_user_dep),
    session: AsyncSession = Depends(get_session),
) -> ChatSummary:
    conversation = await _get_owned_conversation(session, user.id, chat_id)
    conversation.title = request.title.strip()
    await session.commit()
    await session.refresh(conversation)
    return ChatSummary(
        id=conversation.id,
        title=conversation.title,
        created_at=_iso(conversation.created_at),
        updated_at=_iso(conversation.updated_at),
        message_count=len(conversation.messages),
    )


@router.delete("/{chat_id}", status_code=204, summary="Delete chat")
async def delete_chat(
    chat_id: str,
    user: User = Depends(current_user_dep),
    session: AsyncSession = Depends(get_session),
) -> None:
    conversation = await _get_owned_conversation(session, user.id, chat_id)
    await session.delete(conversation)
    await session.commit()


def _share_token(chat_id: str) -> str:
    secret = get_settings().jwt_secret_key.encode()
    return hmac.new(secret, chat_id.encode(), hashlib.sha256).hexdigest()


@router.post("/{chat_id}/share", response_model=ShareResponse, summary="Create read-only share link")
async def share_chat(
    chat_id: str,
    user: User = Depends(current_user_dep),
    session: AsyncSession = Depends(get_session),
) -> ShareResponse:
    await _get_owned_conversation(session, user.id, chat_id)
    token = _share_token(chat_id)
    return ShareResponse(token=token, url=f"/shared/{chat_id}?token={token}")


@router.get("/{chat_id}/shared", response_model=ChatDetailResponse, summary="Read a shared chat (public)")
async def get_shared_chat(
    chat_id: str,
    token: str = Query(...),
    session: AsyncSession = Depends(get_session),
) -> ChatDetailResponse:
    if not hmac.compare_digest(_share_token(chat_id), token):
        raise HTTPException(
            status_code=403,
            detail={"error": {"code": "INVALID_SHARE_TOKEN", "message": "Invalid or expired share link."}},
        )
    conversation = await session.get(Conversation, chat_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail={"error": {"code": "CHAT_NOT_FOUND", "message": "Chat not found."}})
    msgs = (
        await session.execute(
            select(Message)
            .where(Message.conversation_id == chat_id)
            .order_by(Message.created_at.asc())
        )
    ).scalars().all()
    return ChatDetailResponse(
        id=conversation.id,
        title=conversation.title,
        created_at=_iso(conversation.created_at),
        updated_at=_iso(conversation.updated_at),
        messages=[
            ChatMessageItem(
                id=m.id,
                chat_id=m.conversation_id,
                role=m.role,
                content=m.content,
                status=m.status,
                created_at=_iso(m.created_at),
            )
            for m in msgs
        ],
    )
