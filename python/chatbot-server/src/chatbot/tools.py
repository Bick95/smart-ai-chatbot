from __future__ import annotations

from langchain.tools import tool

from src.utils.types.clients import Clients
from src.chatbot.types.agent_tools import AgentTools


def get_agent_tools(clients: Clients) -> AgentTools:
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

    tools = [multiply, divide, add, subtract]

    tools_by_name = {t.name: t for t in tools}

    if len(tools_by_name) != len(tools):
        raise ValueError("Duplicate tool names detected.")

    return AgentTools(
        tools=tools,
        tools_by_name=tools_by_name
    )
