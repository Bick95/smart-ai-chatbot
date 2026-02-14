"""FastAPI application factory and configuration."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.server.routers.stateless_chat import router as stateless_chat_router
from src.utils.clients import create_clients


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create shared clients on startup; agent is created per request."""
    clients = create_clients()
    app.state.clients = clients
    yield
    # No explicit cleanup needed for clients


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

    app.include_router(stateless_chat_router, prefix="/api/v1")

    @app.get("/health")
    def health() -> dict[str, str]:
        """Health check endpoint for load balancers and monitoring."""
        return {"status": "ok"}

    return app


app = create_app()
