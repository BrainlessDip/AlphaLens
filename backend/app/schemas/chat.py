from pydantic import BaseModel, Field


class ChatSummary(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int


class ChatListResponse(BaseModel):
    items: list[ChatSummary]
    total: int


class CreateChatResponse(BaseModel):
    id: str
    title: str


class RenameChatRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=120)


class ShareResponse(BaseModel):
    token: str
    url: str


class ChatMessageItem(BaseModel):
    id: str
    chat_id: str
    role: str
    content: str
    status: str
    created_at: str


class ChatDetailResponse(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    messages: list[ChatMessageItem]
