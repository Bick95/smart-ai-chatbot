"""FastAPI dependencies for the chatbot server."""

from __future__ import annotations

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from langgraph.graph.state import CompiledStateGraph

from src.app_data.ports.chat_port import ChatPort
from src.auth.ports.auth_port import AuthPort
from src.auth.utils.jwt import SubjectPayload, verify_auth_token
from src.chatbot.graph import get_agent
from src.chatbot.state import AgentState
from src.utils.types.clients import Clients

_http_bearer = HTTPBearer(auto_error=False)


def get_clients(request: Request) -> Clients:
    """Retrieve the shared clients from app state."""
    clients: Clients = request.app.state.clients
    return clients


def get_agent_graph(
    clients: Clients = Depends(get_clients),
) -> CompiledStateGraph[AgentState, None, AgentState, AgentState]:
    """Create a fresh agent instance per request to avoid data leakage between users."""
    return get_agent(clients)


def get_auth(request: Request) -> AuthPort:
    """Retrieve the auth adapter from app state."""
    return request.app.state.auth


def get_chat_port(request: Request) -> ChatPort:
    """Retrieve the chat adapter from app state."""
    return request.app.state.chat


def get_current_subject(
    credentials: HTTPAuthorizationCredentials | None = Depends(_http_bearer),
) -> SubjectPayload:
    """Extract and verify the auth JWT from the Authorization header.

    Returns the SubjectPayload if the token is valid. Raises 401 if missing or invalid.
    """
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    subject = verify_auth_token(credentials.credentials)
    if subject is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return subject
