"""Pytest configuration and fixtures."""

import os

# Set env for tests before app import (auth and app_data use mock; no DB needed)
os.environ["OPENAI_API_KEY"] = "sk-test-dummy-for-unit-tests"
os.environ["AUTH_PROVIDER"] = "mock"
os.environ["APP_DATA_PROVIDER"] = "mock"
os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-for-unit-tests-min-32-bytes"

import pytest
from fastapi.testclient import TestClient

from src.auth.utils.jwt import SubjectPayload, SubjectType
from src.server.app import app
from src.server.dependencies import get_agent_graph, get_current_subject


# Dummy subject for tests that bypass auth (e.g. chat logic, path validation)
MOCK_SUBJECT = SubjectPayload(subject_type=SubjectType.USER, subject_id="550e8400-e29b-41d4-a716-446655440000")


def _mock_get_current_subject() -> SubjectPayload:
    """Return a dummy subject for tests that need to bypass auth."""
    return MOCK_SUBJECT


class MockAgent:
    """Minimal mock agent that returns a fixed AIMessage."""

    async def ainvoke(self, state: dict):
        from langchain_core.messages import AIMessage

        return {
            "messages": list(state.get("messages", [])) + [AIMessage(content="Mocked reply")]
        }


@pytest.fixture
def client():
    """Test client with default app. Uses context manager so lifespan runs."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def client_with_mock_agent(client):
    """Test client with mocked agent (no LLM calls) and auth bypass for chat tests."""
    async def override_get_agent_graph():
        return MockAgent()

    app.dependency_overrides[get_agent_graph] = override_get_agent_graph
    app.dependency_overrides[get_current_subject] = _mock_get_current_subject
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def client_with_auth_bypass(client):
    """Test client with auth bypass (for testing path validation, etc.).

    Overrides get_current_subject so requests reach route logic without a real JWT.
    Use for tests that need to verify path/body validation (e.g. invalid UUID).
    """
    app.dependency_overrides[get_current_subject] = _mock_get_current_subject
    yield client
    app.dependency_overrides.clear()
