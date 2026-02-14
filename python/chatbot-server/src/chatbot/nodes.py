from langchain.messages import SystemMessage, ToolMessage
from src.chatbot.state import AgentState, AgentStateUpdate
from src.chatbot.types.llm_models import LLMModelSelection
from src.chatbot.types.agent_nodes import AgentNodes
from src.chatbot.types.agent_tools import AgentTools
from src.utils.types.clients import Clients


# TODO: Adjust the prompts

def get_agent_nodes(clients: Clients, agent_tools: AgentTools) -> AgentNodes:
    model_with_tools = clients.llm_models[LLMModelSelection.STANDARD].bind_tools(
        agent_tools.tools
    )

    async def llm_node(state: AgentState) -> AgentStateUpdate:
        """LLM decides whether to call a tool or not"""
        response = await model_with_tools.ainvoke(
            [
                SystemMessage(
                    content="You are a helpful assistant who uses its tools to assist the user on their tasks."
                )
            ]
            + state["messages"]
        )
        return {"messages": [response]}

    async def tool_node(state: AgentState) -> AgentStateUpdate:
        """Performs the tool call"""
        result = []
        for tool_call in state["messages"][-1].tool_calls:
            tool = agent_tools.tools_by_name[tool_call["name"]]
            observation = await tool.ainvoke(tool_call["args"])
            result.append(
                ToolMessage(
                    content=observation, tool_call_id=tool_call["id"]
                )
            )
        return {"messages": result}

    return {
        "llm_node": llm_node,
        "tool_node": tool_node,
    }
