from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from src.chatbot.nodes import get_agent_nodes
from src.chatbot.state import AgentState
from src.chatbot.tools import get_agent_tools
from src.chatbot.utils import should_continue
from src.utils.types.clients import Clients


def get_agent(
    clients: Clients,
) -> CompiledStateGraph[AgentState, None, AgentState, AgentState]:

    # Construct the tools
    agent_tools = get_agent_tools(clients)
    agent_nodes = get_agent_nodes(clients, agent_tools)

    # Build workflow
    agent_builder = StateGraph(AgentState)

    # Add nodes
    agent_builder.add_node("llm_node", agent_nodes["llm_node"])
    agent_builder.add_node("tool_node", agent_nodes["tool_node"])

    # Add edges to connect nodes
    agent_builder.add_edge(START, "llm_node")
    agent_builder.add_conditional_edges("llm_node", should_continue, ["tool_node", END])
    agent_builder.add_edge("tool_node", "llm_node")

    # Compile the agent
    return agent_builder.compile()
