"""Chat API router."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from langchain_core.messages import AIMessage

from src.server.dependencies import get_agent_graph
from src.server.schemas.chat import ChatRequest, ChatResponse
from src.server.utils import to_langchain_messages


router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    agent=Depends(get_agent_graph),
) -> ChatResponse:
    """
    Send messages to the chatbot and receive a reply.

    Provide the conversation history; the assistant's response will be returned.
    """
    messages = to_langchain_messages([m.model_dump() for m in request.messages])
    # TODO: Add guardrails to prevent abuse or misuse of the API
    result = await agent.ainvoke({"messages": messages})
    result_messages = result["messages"]

    content = ""
    for msg in reversed(result_messages):
        if isinstance(msg, AIMessage) and msg.content:
            content = msg.content if isinstance(msg.content, str) else str(msg.content)
            break

    return ChatResponse(content=content)
