"""FastAPI dependencies for the chatbot server."""

from __future__ import annotations

from fastapi import Depends, Request

from src.chatbot.graph import get_agent
from src.utils.types.clients import Clients


def get_clients(request: Request) -> Clients:
    """Retrieve the shared clients from app state."""
    clients: Clients = request.app.state.clients
    return clients


def get_agent_graph(
    clients: Clients = Depends(get_clients),
):
    """Create a fresh agent instance per request to avoid data leakage between users."""
    return get_agent(clients)
