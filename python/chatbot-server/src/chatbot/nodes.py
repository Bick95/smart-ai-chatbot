from langchain.messages import AIMessage, SystemMessage, ToolMessage

from src.chatbot.prompts import get_prompt_handler
from src.chatbot.state import AgentState, AgentStateUpdate
from src.chatbot.types.agent_nodes import AgentNodes
from src.chatbot.types.agent_tools import AgentTools
from src.chatbot.types.llm_models import LLMModelSelection
from src.utils.logging import get_logger
from src.utils.types.clients import Clients

logger = get_logger(__name__)

prompts_handler = get_prompt_handler()


def get_agent_nodes(clients: Clients, agent_tools: AgentTools) -> AgentNodes:
    model_with_tools = clients.llm_models[LLMModelSelection.STANDARD].bind_tools(
        agent_tools.tools
    )

    async def llm_node(state: AgentState) -> AgentStateUpdate:
        """LLM decides whether to call a tool or not"""
        try:
            response = await model_with_tools.ainvoke(
                [SystemMessage(content=prompts_handler.get("nodes.llm_node.system"))]
                + state["messages"]
            )
            return {"messages": [response]}

        except Exception:
            logger.exception("Error in llm_node. Returning fallback message.")
            return {
                "messages": [
                    AIMessage(content=prompts_handler.get("nodes.llm_node.fallback"))
                ]
            }

    async def tool_node(state: AgentState) -> AgentStateUpdate:
        """Performs the tool call"""
        result = []
        for tool_call in state["messages"][-1].tool_calls:
            try:
                tool = agent_tools.tools_by_name[tool_call["name"]]
                observation = await tool.ainvoke(tool_call["args"])
                result.append(
                    ToolMessage(content=observation, tool_call_id=tool_call["id"])
                )

            except Exception:
                logger.exception(
                    "Error for tool call %s in tool_node. Returning fallback.",
                    tool_call,
                )
                result.append(
                    ToolMessage(
                        content=prompts_handler.get("nodes.tool_node.fallback"),
                        tool_call_id=tool_call["id"],
                    )
                )

        return {"messages": result}

    return {
        "llm_node": llm_node,
        "tool_node": tool_node,
    }
