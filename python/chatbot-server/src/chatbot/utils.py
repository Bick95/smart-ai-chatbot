from typing import Literal
from langgraph.graph import END
from src.chatbot.state import AgentState


def should_continue(state: AgentState) -> Literal["tool_node", END]:
    """Decide if we should continue the loop or stop based upon whether the LLM made a tool call"""

    messages = state["messages"]
    last_message = messages[-1]

    # If the LLM makes a tool call, then route to the tool_node next to perform the tool calls
    if last_message.tool_calls:
        return "tool_node"

    # Otherwise, we stop the loop (i.e. reply to the user)
    return END
