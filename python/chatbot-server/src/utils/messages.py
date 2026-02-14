"""Server utility functions."""

from __future__ import annotations

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from src.utils.logging import get_logger

logger = get_logger(__name__)


def to_langchain_messages(messages: list[dict]) -> list[BaseMessage]:
    """Convert API message format to LangChain messages."""
    result: list[BaseMessage] = []
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "") or ""
        match role:
            case "user":
                result.append(HumanMessage(content=content))
            case "assistant":
                result.append(AIMessage(content=content))
            case "system":
                result.append(SystemMessage(content=content))
            case _:
                logger.warning(
                    "Invalid role %r in message. Expected 'user', 'assistant', or "
                    "'system'. Skipping.",
                    role,
                )
                continue
    return result
