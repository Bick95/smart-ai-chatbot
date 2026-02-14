"""Chat API router."""

from __future__ import annotations

import traceback
from typing import List

from fastapi import APIRouter, Depends
from langchain_core.messages import AIMessage, AnyMessage
from langgraph.graph.state import CompiledStateGraph

from src.chatbot.state import AgentState
from src.server.dependencies import get_agent_graph
from src.server.schemas.chat import ChatRequest, ChatResponse
from src.utils.messages import to_langchain_messages
from src.settings import settings


router = APIRouter(prefix="/chat", tags=["chat"])

_FALLBACK_CONTENT = (
    "Sorry, I cannot answer that right now. Please try again or try something different."
)


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    agent: CompiledStateGraph[AgentState, None, AgentState, AgentState] = Depends(
        get_agent_graph
    ),
) -> ChatResponse:
    """
    Send messages to the chatbot and receive a reply.

    Provide the conversation history; the assistant's response will be returned.
    """
    try:
        messages = to_langchain_messages([m.model_dump() for m in request.messages])

        if not messages:
            raise ValueError("No valid messages provided")

        # TODO: Add guardrails to prevent abuse or misuse of the API

        result_agent_state: AgentState = await agent.ainvoke({"messages": messages})
        result_messages: List[AnyMessage] = result_agent_state["messages"]

        if not result_messages:
            raise ValueError("Agent returned no messages")

        reply: AIMessage = result_messages[-1]

        if settings.DEBUG:
            for msg in result_messages:
                print(
                    f"Message ({msg.type}): {msg.content if msg.content else 'No content'}; "
                    f"Raw message: {msg.model_dump()}"
                )
            print(f"Reply {reply.type}: {reply.content}")

        if not isinstance(reply, AIMessage) or not reply.content:
            raise ValueError(
                f"Expected last message to be AIMessage with content, got {type(reply).__name__}"
            )

        content = (
            reply.content if isinstance(reply.content, str) else str(reply.content)
        )
        return ChatResponse(content=content)

    except Exception as e:
        print(f"Error in chat: {e}")
        if settings.DEBUG:
            print(f"Error details: {traceback.format_exc()}")

        return ChatResponse(content=_FALLBACK_CONTENT)
