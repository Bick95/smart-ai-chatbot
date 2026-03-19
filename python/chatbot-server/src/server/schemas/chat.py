from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, model_validator

from src.app_data.ports.types import MessageRole, ShareRole, SubjectType
from src.utils.validation import Uuid4Str
from src.settings import settings


class ChatMessage(BaseModel):
    """A single message in a conversation."""

    role: MessageRole = Field(
        ...,
        description="Message role: 'user', 'assistant', or 'system'",
    )
    content: str = Field(
        ...,
        description="Message content",
        max_length=settings.MAX_MESSAGE_CONTENT_LENGTH,
    )


def _messages_alternate(messages: list[ChatMessage]) -> bool:
    """Check that user and assistant messages alternate (system only at start)."""
    if not messages:
        return True
    i = 0
    while i < len(messages) and messages[i].role == MessageRole.SYSTEM:
        i += 1
    if i >= len(messages):
        return True  # only system messages
    prev: MessageRole | None = None
    for msg in messages[i:]:
        if msg.role == MessageRole.SYSTEM:
            return False  # system allowed only at start
        if msg.role in (MessageRole.USER, MessageRole.ASSISTANT):
            if prev is not None and msg.role == prev:
                return False
            prev = msg.role
    return True


class ChatRequest(BaseModel):
    """Request body for the chat endpoint."""

    messages: list[ChatMessage] = Field(
        ...,
        description="Conversation history. Messages must alternate between user and assistant (system allowed only at start).",
        min_length=1,
        max_length=settings.MAX_CHAT_MESSAGES,
    )

    @model_validator(mode="after")
    def validate_alternating_order(self) -> "ChatRequest":
        if not _messages_alternate(self.messages):
            raise ValueError(
                "Messages must alternate between 'user' and 'assistant'; "
                "'system' is allowed only at the start"
            )
        return self


class ChatResponse(BaseModel):
    """Response from the chat endpoint."""

    content: str = Field(..., description="The assistant's reply")


# --- Stateful chat API schemas ---


class ChatCreateRequest(BaseModel):
    """Request to create a chat."""

    folder_id: Optional[Uuid4Str] = Field(default=None, description="Optional folder ID")
    title: str | None = Field(default=None, max_length=255)


class ChatUpdateRequest(BaseModel):
    """Request to update a chat (rename and/or move)."""

    title: str | None = Field(default=None, max_length=255)
    folder_id: Optional[Uuid4Str] = Field(
        default=None,
        description="Folder ID; null moves to root; omit to leave unchanged",
    )


class ChatResponseItem(BaseModel):
    """Chat in list/get response."""

    id: Uuid4Str
    owner_subject: str = Field(
        ...,
        description="Owner as 'type:id' (e.g. user:550e8400-e29b-41d4-a716-446655440000)",
    )
    folder_id: Optional[Uuid4Str]
    title: str | None
    created_at: str
    updated_at: str


class ChatListResponse(BaseModel):
    """Paginated list of chats."""

    items: list[ChatResponseItem]
    next_cursor: str | None = None


class ChatMessageResponseItem(BaseModel):
    """Message in list response."""

    id: Uuid4Str
    chat_id: Uuid4Str
    role: MessageRole
    content: str
    created_at: str


class ChatMessageListResponse(BaseModel):
    """Paginated list of messages."""

    items: list[ChatMessageResponseItem]
    next_cursor: str | None = None


class AddMessageRequest(BaseModel):
    """Request to add a message and optionally get AI reply."""

    role: MessageRole = Field(...)
    content: str = Field(..., max_length=settings.MAX_MESSAGE_CONTENT_LENGTH)
    generate_reply: bool = Field(
        default=True,
        description="If true and role is 'user', invoke agent to generate assistant reply",
    )


class AddMessageResponse(BaseModel):
    """Response from adding a message."""

    message: ChatMessageResponseItem
    reply: str | None = Field(
        default=None,
        description="Assistant reply if generate_reply was true",
    )


class ShareRequest(BaseModel):
    """Request to add a share."""

    subject_type: SubjectType = Field(
        ..., description="Subject type (e.g. user, service_account, group)"
    )
    subject_id: Uuid4Str = Field(
        ..., description="Subject ID (e.g. user UUID) to share with"
    )
    role: ShareRole = Field(...)


class ShareResponseItem(BaseModel):
    """Share in list response."""

    chat_id: Uuid4Str
    subject: str = Field(
        ...,
        description="Grantee as 'type:id' (e.g. user:550e8400-e29b-41d4-a716-446655440000)",
    )
    role: ShareRole
    created_at: str


class FolderCreateRequest(BaseModel):
    """Request to create a folder."""

    name: str = Field(..., min_length=1, max_length=255)
    parent_id: Optional[Uuid4Str] = None
    system_prompt: str | None = Field(
        default=None,
        description="Optional system prompt to apply to all chats in this folder",
    )


class FolderPatchRequest(BaseModel):
    """Request to patch a folder (name and/or system_prompt; at least one required)."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    system_prompt: str | None = Field(
        default=None,
        description="Optional system prompt; omit to leave unchanged",
    )

    @model_validator(mode="after")
    def at_least_one_field(self) -> "FolderPatchRequest":
        if "name" not in self.model_fields_set and "system_prompt" not in self.model_fields_set:
            raise ValueError("Provide at least one of name or system_prompt")
        return self


class FolderMoveRequest(BaseModel):
    """Request to move a folder to another parent."""

    parent_id: Optional[Uuid4Str] = Field(
        default=None,
        description="New parent folder ID; null moves to root",
    )


class FolderResponseItem(BaseModel):
    """Folder in list response."""

    id: str
    owner_subject: str = Field(
        ...,
        description="Owner as 'type:id' (e.g. user:550e8400-e29b-41d4-a716-446655440000)",
    )
    parent_id: str | None
    name: str
    system_prompt: str | None = None
    created_at: str
    updated_at: str


class MoveChatToFolderRequest(BaseModel):
    """Request to move chat to folder."""

    folder_id: Optional[Uuid4Str] = Field(default=None, description="Null moves to root")


class UserSearchResponseItem(BaseModel):
    """User in search response (for sharing). Only id and username to avoid leaking email."""

    id: Uuid4Str
    username: str
