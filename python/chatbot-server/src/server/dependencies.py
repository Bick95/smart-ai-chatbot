"""FastAPI dependencies for the chatbot server."""

from __future__ import annotations

from fastapi import Depends, Request
from langgraph.graph.state import CompiledStateGraph

from src.auth.ports.auth_port import AuthPort
from src.chatbot.graph import get_agent
from src.chatbot.state import AgentState
from src.utils.types.clients import Clients


def get_clients(request: Request) -> Clients:
    """Retrieve the shared clients from app state."""
    clients: Clients = request.app.state.clients
    return clients


def get_agent_graph(
    clients: Clients = Depends(get_clients),
) -> CompiledStateGraph[AgentState, None, AgentState, AgentState]:
    """Create a fresh agent instance per request to avoid data leakage between users."""
    return get_agent(clients)


def get_auth(request: Request) -> AuthPort | None:
    """Retrieve the auth adapter from app state (None if auth disabled)."""
    return getattr(request.app.state, "auth", None)
