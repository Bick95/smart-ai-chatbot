"""Chat API router."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from src.server.dependencies import get_agent_graph
from src.server.schemas.chat import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["chat"])


def _to_langchain_messages(messages: list[dict]) -> list[BaseMessage]:
    """Convert API message format to LangChain messages."""
    result: list[BaseMessage] = []
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "") or ""
        if role == "user":
            result.append(HumanMessage(content=content))
        elif role == "assistant":
            result.append(AIMessage(content=content))
        elif role == "system":
            result.append(SystemMessage(content=content))
    return result


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    agent=Depends(get_agent_graph),
) -> ChatResponse:
    """
    Send messages to the chatbot and receive a reply.

    Provide the conversation history; the assistant's response will be returned.
    """
    messages = _to_langchain_messages([m.model_dump() for m in request.messages])
    result = await agent.ainvoke({"messages": messages})
    result_messages = result["messages"]

    content = ""
    for msg in reversed(result_messages):
        if isinstance(msg, AIMessage) and msg.content:
            content = msg.content if isinstance(msg.content, str) else str(msg.content)
            break

    return ChatResponse(content=content)
