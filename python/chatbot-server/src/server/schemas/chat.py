from __future__ import annotations

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """A single message in a conversation."""

    role: str = Field(
        ...,
        description="Message role: 'user', 'assistant', or 'system'",
        pattern="^(user|assistant|system)$",
    )
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    """Request body for the chat endpoint."""

    messages: list[ChatMessage] = Field(
        ...,
        description="Conversation history. The last message should typically be from the user.",
        min_length=1,
    )


class ChatResponse(BaseModel):
    """Response from the chat endpoint."""

    content: str = Field(..., description="The assistant's reply")
