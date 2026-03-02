"""Request/response middleware and error sanitization."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import HTTPException as StarletteHTTPException

from src.settings import settings
from src.utils.logging import get_logger

logger = get_logger(__name__)

SANITIZED_500_MESSAGE = "Internal Server Error"


async def sanitized_http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """
    Sanitize HTTPException responses: 5xx details are never exposed to clients.

    Acts as a fallback so any 5xx raised with dynamic detail gets a generic message.
    """
    if exc.status_code >= 500:
        logger.warning(
            "Sanitizing HTTPException %s for %s %s: %s",
            exc.status_code,
            request.method,
            request.url.path,
            type(exc).__name__,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": SANITIZED_500_MESSAGE},
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log incoming requests and outgoing responses. Tracks duration."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Any]
    ) -> Any:
        start = time.perf_counter()
        logger.debug("Request: %s %s", request.method, request.url.path)

        response = await call_next(request)

        duration_ms = (time.perf_counter() - start) * 1000
        logger.debug(
            "Response: %s for %s %s (%.1fms)",
            response.status_code,
            request.method,
            request.url.path,
            duration_ms,
        )
        return response


async def sanitized_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch unhandled exceptions and return a sanitized 500 response.

    Full exception details are logged for debugging; clients receive only a
    generic message to avoid leaking internal information.
    """
    # In production, avoid logging exception message or traceback
    if settings.DEBUG:
        logger.exception(
            "Unhandled exception for %s %s: %s",
            request.method,
            request.url.path,
            exc,
            exc_info=True,
        )
    else:
        logger.error(
            "Unhandled exception for %s %s: %s",
            request.method,
            request.url.path,
            type(exc).__name__,
            exc_info=False,
        )
    return JSONResponse(
        status_code=500,
        content={"detail": SANITIZED_500_MESSAGE},
    )
