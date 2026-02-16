"""Tests for API endpoints."""

import pytest


@pytest.mark.unit
class TestHealthEndpoint:
    def test_health_returns_ok(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


@pytest.mark.unit
class TestStatelessChatEndpoint:
    def test_stateless_chat_returns_response(self, client_with_mock_agent):
        response = client_with_mock_agent.post(
            "/api/v1/stateless_chat",
            json={"messages": [{"role": "user", "content": "Hello"}]},
        )
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert data["content"] == "Mocked reply"

    def test_stateless_chat_rejects_empty_messages(self, client_with_mock_agent):
        response = client_with_mock_agent.post(
            "/api/v1/stateless_chat",
            json={"messages": []},
        )
        assert response.status_code == 422

    def test_stateless_chat_rejects_invalid_role(self, client_with_mock_agent):
        response = client_with_mock_agent.post(
            "/api/v1/stateless_chat",
            json={"messages": [{"role": "invalid", "content": "hi"}]},
        )
        assert response.status_code == 422
