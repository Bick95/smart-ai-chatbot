"""Tests for API endpoints."""

import pytest


@pytest.mark.unit
class TestAuthEndpoints:
    """Auth endpoints (auth is mandatory)."""

    def test_signup_returns_user_and_tokens(self, client):
        """Signup with mock auth returns user and JWTs."""
        response = client.post(
            "/api/v1/auth/signup",
            json={"email": "a@b.com", "username": "u", "password": "password123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert data["user"]["email"] == "a@b.com"
        assert "auth_token" in data
        assert "refresh_token" in data

    def test_login_returns_401_for_invalid_credentials(self, client):
        """Login with unknown user returns 401."""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "unknown@b.com", "password": "password123"},
        )
        assert response.status_code == 401

    def test_signup_rejects_short_password(self, client):
        response = client.post(
            "/api/v1/auth/signup",
            json={"email": "a@b.com", "username": "u", "password": "short"},
        )
        assert response.status_code == 422

    def test_login_rejects_short_password_without_verification(self, client):
        """Password < 8 chars rejected by validation (422) before auth attempt."""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "a@b.com", "password": "short"},
        )
        assert response.status_code == 422

    def test_get_user_returns_401_without_token(self, client):
        """Protected endpoints require Bearer token."""
        response = client.get(
            "/api/v1/auth/users/550e8400-e29b-41d4-a716-446655440000"
        )
        assert response.status_code == 401

    def test_stateless_chat_returns_401_without_token(self, client):
        """Chat endpoint requires Bearer token."""
        response = client.post(
            "/api/v1/stateless_chat",
            json={"messages": [{"role": "user", "content": "Hi"}]},
        )
        assert response.status_code == 401

    def test_get_user_rejects_invalid_uuid_format(self, client_with_auth_bypass):
        """Path validation runs before auth; invalid UUID returns 422."""
        response = client_with_auth_bypass.get("/api/v1/auth/users/not-a-uuid")
        assert response.status_code == 422


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
