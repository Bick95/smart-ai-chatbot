"""FastAPI application factory and configuration."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import HTTPException as StarletteHTTPException

from src.auth.factory import create_auth_adapter
from src.chatbot.prompts import (
    FilePromptSource,
    HttpPromptSource,
    PromptHandler,
    get_prompt_handler,
    set_prompt_handler,
)
from src.server.middleware import (
    RequestLoggingMiddleware,
    sanitized_exception_handler,
    sanitized_http_exception_handler,
)
from src.server.routers.auth import router as auth_router
from src.server.routers.stateless_chat import router as stateless_chat_router
from src.settings import settings
from src.utils.clients import create_clients


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create shared clients on startup; agent is created per request."""
    clients = create_clients()
    app.state.clients = clients

    # Auth adapter (hexagonal: postgres, supabase, or mock for tests)
    auth_adapter, auth_cleanup = await create_auth_adapter()
    app.state.auth = auth_adapter

    # Optional: configure prompt handler with API source for live refresh
    if settings.PROMPT_API_URL:
        prompt_handler = PromptHandler(
            sources=[
                HttpPromptSource(
                    settings.PROMPT_API_URL,
                    refresh_interval_seconds=settings.PROMPT_REFRESH_INTERVAL_SECONDS,
                ),
                FilePromptSource(),
            ]
        )
        set_prompt_handler(prompt_handler)
        prompt_handler.start_background_refresh()

    yield

    # Stop prompt refresh if it was started
    get_prompt_handler().stop_background_refresh()

    # Close auth resources (asyncpg.Pool when postgres or supabase+DB)
    if auth_cleanup is not None:
        await auth_cleanup.close()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Chatbot API",
        description="Smart AI chatbot with tool-calling support",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.ENABLE_DOCS else None,
        redoc_url="/redoc" if settings.ENABLE_DOCS else None,
    )

    # Exception handlers (most specific wins; registration order does not matter):
    # - HTTPException: sanitizes 5xx details, passes 4xx through as-is
    # - Exception: catch-all for RuntimeError, DB errors, etc.; returns generic 500
    app.add_exception_handler(Exception, sanitized_exception_handler)
    app.add_exception_handler(
        StarletteHTTPException, sanitized_http_exception_handler
    )

    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(stateless_chat_router, prefix="/api/v1")

    @app.get("/health")
    def health() -> dict[str, str]:
        """Health check endpoint for load balancers and monitoring."""
        return {"status": "ok"}

    return app


app = create_app()
