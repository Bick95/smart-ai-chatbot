from langchain.messages import SystemMessage, ToolMessage
from src.chatbot.state import AgentState, AgentStateUpdate
from src.chatbot.types.llm_models import LLMModelSelection
from src.chatbot.types.clients import Clients
from src.chatbot.types.agent_nodes import AgentNodes


# TODO: Add tools
# TODO: Turn nodes async

def get_agent_nodes(clients: Clients) -> AgentNodes:

    def llm_node(state: AgentState) -> AgentStateUpdate:
        """LLM decides whether to call a tool or not"""

        model_with_tools = clients.llm_models[LLMModelSelection.STANDARD].bind_tools(tools)

        return {
            "messages": [
                model_with_tools.invoke(
                    [
                        SystemMessage(
                            content="You are a helpful assistant tasked with performing summaries of provided input texts. To compute summaries of a given input text, always use the dedicated tool."
                        )
                    ]
                    + state["messages"]
                )
            ],
        }

    def tool_node(state: AgentState) -> AgentStateUpdate:
        """Performs the tool call"""

        result = []
        # TODO: Make it async
        for tool_call in state["messages"][-1].tool_calls:
            tool = tools_by_name[tool_call["name"]]
            observation = tool.invoke(tool_call["args"])
            result.append(ToolMessage(content=observation, tool_call_id=tool_call["id"]))
        return {"messages": result}

    return {
        "llm_node": llm_node,
        "tool_node": tool_node,
    }
