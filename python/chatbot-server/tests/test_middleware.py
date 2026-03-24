"""Tests for request/response middleware and error sanitization."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.requests import HTTPException as StarletteHTTPException

from src.server.middleware import (
    SANITIZED_500_MESSAGE,
    RequestLoggingMiddleware,
    sanitized_exception_handler,
    sanitized_http_exception_handler,
)


@pytest.fixture
def app_with_handler():
    """Minimal app with sanitized exception handlers for testing."""
    app = FastAPI()
    app.add_exception_handler(Exception, sanitized_exception_handler)
    app.add_exception_handler(StarletteHTTPException, sanitized_http_exception_handler)

    @app.get("/ok")
    def ok():
        return {"status": "ok"}

    @app.get("/raise")
    def raise_error():
        raise RuntimeError("internal secret path /var/secrets")

    @app.get("/raise_5xx")
    def raise_5xx():
        raise StarletteHTTPException(
            status_code=503,
            detail="Internal leak: connection refused to db.example.com",
        )

    return app


@pytest.fixture
def client_with_handler(app_with_handler):
    return TestClient(app_with_handler, raise_server_exceptions=False)


@pytest.mark.unit
class TestSanitizedExceptionHandler:
    def test_unhandled_exception_returns_500_with_generic_message(
        self, client_with_handler
    ):
        response = client_with_handler.get("/raise")
        assert response.status_code == 500
        assert response.json() == {"detail": SANITIZED_500_MESSAGE}

    def test_exception_details_not_exposed(self, client_with_handler):
        response = client_with_handler.get("/raise")
        body = response.text
        assert "internal secret" not in body
        assert "/var/secrets" not in body

    def test_5xx_http_exception_detail_sanitized(self, client_with_handler):
        """5xx HTTPException details are never exposed to clients."""
        response = client_with_handler.get("/raise_5xx")
        assert response.status_code == 503
        assert response.json() == {"detail": SANITIZED_500_MESSAGE}
        assert "connection refused" not in response.text
        assert "db.example.com" not in response.text


@pytest.mark.unit
class TestRequestLoggingMiddleware:
    def test_request_and_response_logged(self, app_with_handler):
        app_with_handler.add_middleware(RequestLoggingMiddleware)
        client = TestClient(app_with_handler)
        response = client.get("/ok")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
