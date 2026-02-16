from __future__ import annotations

from datetime import datetime

from langchain.messages import AIMessage, HumanMessage, SystemMessage
from langchain.tools import tool

from src.chatbot.prompts import get_prompt_handler
from src.chatbot.types.agent_tools import AgentTools
from src.chatbot.types.llm_models import LLMModelSelection
from src.utils.types.clients import Clients


def get_agent_tools(clients: Clients) -> AgentTools:

    model_small = clients.llm_models[LLMModelSelection.SMALL]

    @tool
    async def multiply(a: int, b: int) -> int:
        """Multiply `a` and `b`."""
        return a * b

    @tool
    async def divide(a: int, b: int) -> float:
        """Divide `a` and `b`."""
        return a / b

    @tool
    async def add(a: int, b: int) -> int:
        """Add `a` and `b`."""
        return a + b

    @tool
    async def subtract(a: int, b: int) -> float:
        """Subtract `b` from `a`."""
        return b - a

    @tool
    async def get_current_datetime() -> str:
        """
        Return the current date and time (uses the system's local time).
        Use this when the user asks what day it is, what date, what time, or similar.
        """
        return datetime.now().strftime("%A, %B %d, %Y, %H:%M:%S")

    @tool
    async def summarize_text(input_text: str) -> str:
        """
        Produce a plain, pure summary of the given input text.
        Use this when the user asks to summarize text, articles, or documents.
        """
        if not input_text:
            return ""

        prompts_handler = get_prompt_handler()
        messages = [
            SystemMessage(content=prompts_handler.get("tools.summarize_text.system")),
            HumanMessage(content=input_text),
        ]

        response: AIMessage = await model_small.ainvoke(messages)

        return response.content if isinstance(response.content, str) else str(response.content)

    tools = [multiply, divide, add, subtract, get_current_datetime, summarize_text]

    tools_by_name = {t.name: t for t in tools}

    if len(tools_by_name) != len(tools):
        raise ValueError("Duplicate tool names detected.")

    return AgentTools(
        tools=tools,
        tools_by_name=tools_by_name
    )
