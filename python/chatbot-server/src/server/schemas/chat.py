from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from src.settings import settings


class ChatMessage(BaseModel):
    """A single message in a conversation."""

    role: str = Field(
        ...,
        description="Message role: 'user', 'assistant', or 'system'",
        pattern="^(user|assistant|system)$",
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
    while i < len(messages) and messages[i].role == "system":
        i += 1
    if i >= len(messages):
        return True  # only system messages
    prev: str | None = None
    for msg in messages[i:]:
        if msg.role == "system":
            return False  # system allowed only at start
        if msg.role in ("user", "assistant"):
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
