"""FastAPI dependencies for the chatbot server."""

from __future__ import annotations

from fastapi import Request

from src.utils.types.clients import Clients


def get_clients(request: Request) -> Clients:
    """Retrieve the shared clients from app state."""
    clients: Clients = request.app.state.clients
    return clients


def get_agent_graph(request: Request):
    """Retrieve the compiled agent graph from app state."""
    return request.app.state.agent
