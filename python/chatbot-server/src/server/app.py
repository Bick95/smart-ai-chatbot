"""FastAPI application factory and configuration."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import HTTPException as StarletteHTTPException

from src.app_data.factory import create_chat_adapter
from src.auth.factory import create_auth_adapter
from src.utils.logging import get_logger
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
from src.server.migrations_startup import run_migrations_on_startup
from src.server.routers.auth import router as auth_router
from src.server.routers.stateful_chat import (
    folders_router,
    router as stateful_chat_router,
    users_router,
)
from src.server.routers.stateless_chat import router as stateless_chat_router
from src.settings import settings
from src.utils.clients import create_clients


logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create shared clients on startup; agent is created per request."""
    logger.info("Server starting up")

    await run_migrations_on_startup()

    logger.info("Creating LLM clients")
    clients = create_clients()
    app.state.clients = clients

    logger.info("Initializing auth adapter (%s)", settings.AUTH_PROVIDER.lower())
    auth_adapter, auth_pool = await create_auth_adapter()
    app.state.auth = auth_adapter

    logger.info("Initializing app data adapter (%s)", settings.APP_DATA_PROVIDER.lower())
    chat_adapter, chat_cleanup = await create_chat_adapter(existing_pool=auth_pool)
    app.state.chat = chat_adapter

    if settings.PROMPT_API_URL:
        logger.info("Configuring prompt handler with API source")
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

    logger.info("Startup successful")

    yield

    logger.info("Shutting down...")

    get_prompt_handler().stop_background_refresh()

    if chat_cleanup is not None:
        logger.info("Closing app data resources")
        await chat_cleanup.close()

    if auth_pool is not None:
        logger.info("Closing auth resources")
        await auth_pool.close()

    logger.info("Shutdown successful")


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
    app.include_router(stateful_chat_router, prefix="/api/v1")
    app.include_router(folders_router, prefix="/api/v1")
    app.include_router(users_router, prefix="/api/v1")

    @app.get("/health")
    def health() -> dict[str, str]:
        """Health check endpoint for load balancers and monitoring."""
        return {"status": "ok"}

    return app


app = create_app()
