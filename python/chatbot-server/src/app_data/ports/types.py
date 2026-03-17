"""App data domain types."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

from src.utils.validation import Uuid4Str


class SubjectType(str, Enum):
    """Known subject types for authorization. Used for owners and grantees."""

    USER = "user"
    SERVICE_ACCOUNT = "service_account"
    GROUP = "group"


class ShareRole(str, Enum):
    """Role for shared chat access."""

    VIEWER = "viewer"
    EDITOR = "editor"


class MessageRole(str, Enum):
    """Role of a chat message."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Subject(BaseModel):
    """Actor performing an action. Used for authorization."""

    model_config = ConfigDict(frozen=True)

    subject_type: SubjectType = Field(
        ...,
        description="Subject type: user, service_account, group, etc.",
    )
    subject_id: Uuid4Str = Field(..., description="Subject ID (UUID-v4)")


class Chat(BaseModel):
    """A chat conversation."""

    id: Uuid4Str
    owner_subject_type: SubjectType = Field(...)
    owner_subject_id: Uuid4Str
    folder_id: str | None = None
    title: str | None = None
    created_at: datetime
    updated_at: datetime


class ChatMessage(BaseModel):
    """A single message in a chat."""

    id: Uuid4Str
    chat_id: Uuid4Str
    role: MessageRole
    content: str = Field(..., min_length=0)
    created_at: datetime


class ChatShare(BaseModel):
    """A share granting a subject access to a chat."""

    chat_id: Uuid4Str
    subject_type: SubjectType = Field(...)
    subject_id: Uuid4Str
    role: ShareRole
    created_at: datetime


class Folder(BaseModel):
    """A folder for organizing chats (supports nesting)."""

    id: Uuid4Str
    owner_subject_type: SubjectType = Field(...)
    owner_subject_id: Uuid4Str
    parent_id: str | None = None
    name: str = Field(..., min_length=1)
    system_prompt: str | None = Field(
        default=None,
        description="Optional system prompt to apply to all chats in this folder",
    )
    created_at: datetime
    updated_at: datetime


T = TypeVar("T")


class PaginatedResult(BaseModel, Generic[T]):
    """Paginated result with optional next cursor."""

    items: list[T]
    next_cursor: str | None = None
    total: int | None = None
