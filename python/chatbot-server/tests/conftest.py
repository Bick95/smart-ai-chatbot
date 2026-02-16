"""Pytest configuration and fixtures."""

import os

# Set dummy API key for tests if not present (avoids failures when .env is missing)
os.environ.setdefault("OPENAI_API_KEY", "sk-test-dummy-for-unit-tests")

import pytest
from fastapi.testclient import TestClient

from src.server.app import app
from src.server.dependencies import get_agent_graph


class MockAgent:
    """Minimal mock agent that returns a fixed AIMessage."""

    async def ainvoke(self, state: dict):
        from langchain_core.messages import AIMessage

        return {
            "messages": list(state.get("messages", [])) + [AIMessage(content="Mocked reply")]
        }


@pytest.fixture
def client():
    """Test client with default app."""
    return TestClient(app)


@pytest.fixture
def client_with_mock_agent(client):
    """Test client with mocked agent (no LLM calls)."""
    async def override_get_agent_graph():
        return MockAgent()

    app.dependency_overrides[get_agent_graph] = override_get_agent_graph
    yield client
    app.dependency_overrides.clear()
