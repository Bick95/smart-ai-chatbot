"""Server utility functions."""

from __future__ import annotations

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage


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
                print(
                    f"Invalid role: {role} found in one message. Expected 'user', "
                    "'assistant', or 'system'. Going to skip this message."
                )
                continue
    return result
