"""App data domain types."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

from src.utils.validation import Uuid4Str, validate_uuid4


class SubjectType(str, Enum):
    """Known subject types for authorization. Used for owners and grantees."""

    USER = "user"
    SERVICE_ACCOUNT = "service_account"
    GROUP = "group"


SUBJECT_SEP = ":"


def to_subject_str(subject_type: str, subject_id: str) -> str:
    """Build subject string from type and id. Used for DB storage and RLS."""
    return f"{subject_type}{SUBJECT_SEP}{subject_id}"


def parse_subject_str(s: str) -> tuple[str, str]:
    """Parse subject string into (subject_type, subject_id). Raises ValueError if invalid."""
    if not s or not isinstance(s, str) or SUBJECT_SEP not in s:
        raise ValueError(f"Invalid subject format: {s!r}")
    parts = s.split(SUBJECT_SEP, 1)
    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise ValueError(f"Invalid subject format: {s!r}")
    try:
        SubjectType(parts[0])
    except ValueError:
        valid = [st.value for st in SubjectType]
        raise ValueError(
            f"subject_type must be one of {valid}, got {parts[0]!r}"
        ) from None
    validate_uuid4(parts[1], field_name="subject_id")
    return (parts[0], parts[1])


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

    def to_str(self) -> str:
        """Serialize to 'type:id' format for DB and comparisons."""
        return to_subject_str(
            self.subject_type.value
            if hasattr(self.subject_type, "value")
            else str(self.subject_type),
            self.subject_id,
        )

    @classmethod
    def from_str(cls, s: str) -> Subject:
        """Parse from 'type:id' format."""
        subject_type_str, subject_id = parse_subject_str(s)
        return cls(
            subject_type=SubjectType(subject_type_str),
            subject_id=subject_id,
        )


class Chat(BaseModel):
    """A chat conversation."""

    id: Uuid4Str
    owner_subject: str = Field(
        ...,
        description="Subject as 'type:id' (e.g. user:550e8400-e29b-41d4-a716-446655440000)",
    )
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
    subject: str = Field(
        ...,
        description="Grantee as 'type:id' (e.g. user:550e8400-e29b-41d4-a716-446655440000)",
    )
    role: ShareRole
    created_at: datetime


class Folder(BaseModel):
    """A folder for organizing chats (supports nesting)."""

    id: Uuid4Str
    owner_subject: str = Field(
        ...,
        description="Subject as 'type:id' (e.g. user:550e8400-e29b-41d4-a716-446655440000)",
    )
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
