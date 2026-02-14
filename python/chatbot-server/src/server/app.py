"""FastAPI application factory and configuration."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.chatbot.graph import get_agent
from src.server.routers.chat import router as chat_router
from src.utils.clients import create_clients


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create shared clients and agent on startup; cleanup on shutdown."""
    clients = create_clients()
    agent = get_agent(clients)
    app.state.clients = clients
    app.state.agent = agent
    yield
    # No explicit cleanup needed for clients/agent


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Chatbot API",
        description="Smart AI chatbot with tool-calling support",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(chat_router, prefix="/api/v1")

    @app.get("/health")
    def health() -> dict[str, str]:
        """Health check endpoint for load balancers and monitoring."""
        return {"status": "ok"}

    return app


app = create_app()
