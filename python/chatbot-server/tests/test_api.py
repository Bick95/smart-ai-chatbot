"""Tests for API endpoints."""

from unittest.mock import patch

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

    def test_signup_requires_invite_key_when_configured(self, client):
        """When SIGNUP_INVITE_KEY is set, signup requires matching invite_key."""
        from pydantic import SecretStr

        from src.settings import settings

        with patch.object(settings, "SIGNUP_INVITE_KEY", SecretStr("my-secret-invite")):
            # Without invite_key -> 403
            r = client.post(
                "/api/v1/auth/signup",
                json={
                    "email": "new@b.com",
                    "username": "newuser",
                    "password": "password123",
                },
            )
            assert r.status_code == 403
            assert "invite" in r.json()["detail"].lower()

            # With wrong invite_key -> 403
            r = client.post(
                "/api/v1/auth/signup",
                json={
                    "email": "new@b.com",
                    "username": "newuser",
                    "password": "password123",
                    "invite_key": "wrong-key",
                },
            )
            assert r.status_code == 403

            # With correct invite_key -> 200
            r = client.post(
                "/api/v1/auth/signup",
                json={
                    "email": "invited@b.com",
                    "username": "inviteduser",
                    "password": "password123",
                    "invite_key": "my-secret-invite",
                },
            )
            assert r.status_code == 200
            assert r.json()["user"]["email"] == "invited@b.com"

    def test_signup_rejects_short_password(self, client):
        response = client.post(
            "/api/v1/auth/signup",
            json={"email": "a@b.com", "username": "u", "password": "short"},
        )
        assert response.status_code == 422

    def test_signup_rejects_invalid_email_format(self, client):
        """Email with suspicious/invalid characters is rejected (422)."""
        response = client.post(
            "/api/v1/auth/signup",
            json={
                "email": "user'; DROP TABLE users;--@x.com",
                "username": "validuser",
                "password": "password123",
            },
        )
        assert response.status_code == 422

    def test_signup_rejects_invalid_username_format(self, client):
        """Username with non-allowed characters is rejected (422)."""
        response = client.post(
            "/api/v1/auth/signup",
            json={
                "email": "user@example.com",
                "username": "user<script>alert(1)</script>",
                "password": "password123",
            },
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


@pytest.mark.unit
class TestStatefulChatEndpoints:
    """Stateful chat endpoints (chats, messages, folders, shares)."""

    def test_create_chat(self, client_with_auth_bypass):
        """Create chat returns chat with id."""
        response = client_with_auth_bypass.post("/api/v1/chats", json={})
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["owner_subject_type"] == "user"
        assert data["owner_subject_id"] == "550e8400-e29b-41d4-a716-446655440000"

    def test_rename_and_move_chat(self, client_with_auth_bypass):
        """Rename chat and move to folder."""
        r1 = client_with_auth_bypass.post("/api/v1/chats", json={})
        assert r1.status_code == 200
        chat_id = r1.json()["id"]
        r2 = client_with_auth_bypass.post(
            "/api/v1/folders", json={"name": "My Folder"}
        )
        assert r2.status_code == 200
        folder_id = r2.json()["id"]
        # Rename
        r3 = client_with_auth_bypass.patch(
            f"/api/v1/chats/{chat_id}",
            json={"title": "My Chat"},
        )
        assert r3.status_code == 200
        assert r3.json()["title"] == "My Chat"
        # Move to folder
        r4 = client_with_auth_bypass.patch(
            f"/api/v1/chats/{chat_id}",
            json={"folder_id": folder_id},
        )
        assert r4.status_code == 200
        assert r4.json()["folder_id"] == folder_id
        assert r4.json()["title"] == "My Chat"
        # Move to root
        r5 = client_with_auth_bypass.patch(
            f"/api/v1/chats/{chat_id}/folder",
            json={"folder_id": None},
        )
        assert r5.status_code == 200
        assert r5.json()["folder_id"] is None

    def test_delete_chat(self, client_with_auth_bypass):
        """Delete chat returns 204."""
        r1 = client_with_auth_bypass.post("/api/v1/chats", json={})
        assert r1.status_code == 200
        chat_id = r1.json()["id"]
        r2 = client_with_auth_bypass.delete(f"/api/v1/chats/{chat_id}")
        assert r2.status_code == 204
        r3 = client_with_auth_bypass.get(f"/api/v1/chats/{chat_id}")
        assert r3.status_code == 404

    def test_list_chats(self, client_with_auth_bypass):
        """List chats returns paginated items."""
        response = client_with_auth_bypass.get("/api/v1/chats")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)

    def test_create_folder(self, client_with_auth_bypass):
        """Create folder returns folder with id."""
        response = client_with_auth_bypass.post(
            "/api/v1/folders", json={"name": "My Folder"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "My Folder"
        assert "id" in data

    def test_move_folder(self, client_with_auth_bypass):
        """Move folder to root and to another folder."""
        r1 = client_with_auth_bypass.post(
            "/api/v1/folders", json={"name": "Parent"}
        )
        assert r1.status_code == 200
        parent_id = r1.json()["id"]
        r2 = client_with_auth_bypass.post(
            "/api/v1/folders", json={"name": "Child", "parent_id": parent_id}
        )
        assert r2.status_code == 200
        child_id = r2.json()["id"]
        assert r2.json()["parent_id"] == parent_id
        # Move child to root
        r3 = client_with_auth_bypass.patch(
            f"/api/v1/folders/{child_id}/parent", json={"parent_id": None}
        )
        assert r3.status_code == 200
        assert r3.json()["parent_id"] is None
        # Move child back into parent
        r4 = client_with_auth_bypass.patch(
            f"/api/v1/folders/{child_id}/parent", json={"parent_id": parent_id}
        )
        assert r4.status_code == 200
        assert r4.json()["parent_id"] == parent_id

    def test_user_search(self, client_with_auth_bypass):
        """User search returns list (may be empty)."""
        response = client_with_auth_bypass.get("/api/v1/users/search?q=test")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_add_and_remove_share(self, client_with_auth_bypass):
        """Add share with subject_type/subject_id, list, then remove."""
        # Create chat as owner (MOCK_SUBJECT)
        r1 = client_with_auth_bypass.post("/api/v1/chats", json={})
        assert r1.status_code == 200
        chat_id = r1.json()["id"]
        grantee_id = "660e8400-e29b-41d4-a716-446655440001"
        # Add share
        r2 = client_with_auth_bypass.post(
            f"/api/v1/chats/{chat_id}/shares",
            json={"subject_type": "user", "subject_id": grantee_id, "role": "viewer"},
        )
        assert r2.status_code == 200
        assert r2.json()["subject_type"] == "user"
        assert r2.json()["subject_id"] == grantee_id
        assert r2.json()["role"] == "viewer"
        # List shares
        r3 = client_with_auth_bypass.get(f"/api/v1/chats/{chat_id}/shares")
        assert r3.status_code == 200
        shares = r3.json()
        assert len(shares) == 1
        assert shares[0]["subject_type"] == "user"
        assert shares[0]["subject_id"] == grantee_id
        # Remove share (new path: /chats/{id}/shares/{subject_type}/{subject_id})
        r4 = client_with_auth_bypass.delete(
            f"/api/v1/chats/{chat_id}/shares/user/{grantee_id}"
        )
        assert r4.status_code == 204
        r5 = client_with_auth_bypass.get(f"/api/v1/chats/{chat_id}/shares")
        assert r5.status_code == 200
        assert len(r5.json()) == 0
