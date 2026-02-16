"""Stateless chat API router."""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends
from langchain_core.messages import AIMessage, AnyMessage
from langgraph.graph.state import CompiledStateGraph

from src.chatbot.prompts import get_prompt_handler
from src.chatbot.state import AgentState
from src.server.dependencies import get_agent_graph
from src.server.schemas.chat import ChatRequest, ChatResponse
from src.settings import settings
from src.utils.logging import get_logger
from src.utils.messages import to_langchain_messages

logger = get_logger(__name__)

router = APIRouter(prefix="/stateless_chat", tags=["stateless_chat"])


@router.post("", response_model=ChatResponse)
async def stateless_chat(
    request: ChatRequest,
    agent: CompiledStateGraph[AgentState, None, AgentState, AgentState] = Depends(
        get_agent_graph
    ),
) -> ChatResponse:
    """
    Stateless chat: send messages and receive a reply.

    You must provide the full conversation history each time.
    No session state is kept between requests.
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
                logger.debug(
                    "Message (%s): %s; Raw: %s",
                    msg.type,
                    msg.content if msg.content else "No content",
                    msg.model_dump(),
                )
            logger.debug("Reply %s: %s", reply.type, reply.content)

        if not isinstance(reply, AIMessage) or not reply.content:
            raise ValueError(
                f"Expected last message to be AIMessage with content, got {type(reply).__name__}"
            )

        content = (
            reply.content if isinstance(reply.content, str) else str(reply.content)
        )
        return ChatResponse(content=content)

    except Exception:
        logger.exception("Error in stateless_chat.")

        return ChatResponse(
            content=get_prompt_handler().get("server.stateless_chat.fallback")
        )
