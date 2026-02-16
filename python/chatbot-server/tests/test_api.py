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

    def test_stateless_chat_accepts_alternating_history(self, client_with_mock_agent):
        response = client_with_mock_agent.post(
            "/api/v1/stateless_chat",
            json={
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "system", "content": "Be kind."},
                    {"role": "user", "content": "hi"},
                    {"role": "assistant", "content": "hello"},
                    {"role": "user", "content": "what is 2+2?"},
                ]
            },
        )
        assert response.status_code == 200
        assert response.json()["content"] == "Mocked reply"

    def test_stateless_chat_rejects_non_alternating_messages(self, client_with_mock_agent):
        response = client_with_mock_agent.post(
            "/api/v1/stateless_chat",
            json={
                "messages": [
                    {"role": "user", "content": "u1"},
                    {"role": "user", "content": "u2"},
                ]
            },
        )
        assert response.status_code == 422

    def test_stateless_chat_rejects_intermediate_system_message(self, client_with_mock_agent):
        response = client_with_mock_agent.post(
            "/api/v1/stateless_chat",
            json={
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "system", "content": "Be kind."},
                    {"role": "user", "content": "hi"},
                    {"role": "assistant", "content": "hello"},
                    {"role": "system", "content": "Don't forget to be kind."},
                    {"role": "user", "content": "what is 2+2?"},
                ]
            },
        )
        assert response.status_code == 422
