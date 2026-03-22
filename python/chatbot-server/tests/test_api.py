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

    def test_login_returns_tokens_on_valid_credentials(self, client):
        """Login with valid credentials returns user and tokens."""
        client.post(
            "/api/v1/auth/signup",
            json={"email": "login@test.com", "username": "loginuser", "password": "password123"},
        )
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "login@test.com", "password": "password123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["email"] == "login@test.com"
        assert "auth_token" in data
        assert "refresh_token" in data

    def test_refresh_returns_new_tokens(self, client):
        """Refresh with valid token returns new auth and refresh tokens."""
        signup = client.post(
            "/api/v1/auth/signup",
            json={"email": "refresh@test.com", "username": "refreshuser", "password": "password123"},
        )
        refresh_token = signup.json()["refresh_token"]
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert response.status_code == 200
        data = response.json()
        assert "auth_token" in data
        assert "refresh_token" in data
        assert data["user"]["email"] == "refresh@test.com"

    def test_get_user_with_valid_token(self, client):
        """Get user returns own user when authenticated."""
        signup = client.post(
            "/api/v1/auth/signup",
            json={"email": "getuser@test.com", "username": "getuser", "password": "password123"},
        )
        auth_token = signup.json()["auth_token"]
        user_id = signup.json()["user"]["id"]
        response = client.get(
            f"/api/v1/auth/users/{user_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        assert response.json()["email"] == "getuser@test.com"

    def test_update_username_with_valid_token(self, client):
        """Update username returns updated user."""
        signup = client.post(
            "/api/v1/auth/signup",
            json={"email": "upduser@test.com", "username": "oldname", "password": "password123"},
        )
        auth_token = signup.json()["auth_token"]
        user_id = signup.json()["user"]["id"]
        response = client.patch(
            f"/api/v1/auth/users/{user_id}/username",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"username": "newname"},
        )
        assert response.status_code == 200
        assert response.json()["username"] == "newname"

    def test_update_password_with_valid_token(self, client):
        """Update password succeeds and allows login with new password."""
        signup = client.post(
            "/api/v1/auth/signup",
            json={"email": "pwduser@test.com", "username": "pwduser", "password": "oldpass123"},
        )
        auth_token = signup.json()["auth_token"]
        user_id = signup.json()["user"]["id"]
        r = client.patch(
            f"/api/v1/auth/users/{user_id}/password",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"password": "newpass456"},
        )
        assert r.status_code == 200
        assert client.post(
            "/api/v1/auth/login",
            json={"email": "pwduser@test.com", "password": "newpass456"},
        ).status_code == 200

    def test_delete_user_with_valid_token(self, client):
        """Delete user removes account."""
        signup = client.post(
            "/api/v1/auth/signup",
            json={"email": "deluser@test.com", "username": "deluser", "password": "password123"},
        )
        auth_token = signup.json()["auth_token"]
        user_id = signup.json()["user"]["id"]
        r = client.delete(
            f"/api/v1/auth/users/{user_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert r.status_code == 200
        assert client.post(
            "/api/v1/auth/login",
            json={"email": "deluser@test.com", "password": "password123"},
        ).status_code == 401

    def test_update_email_with_valid_token(self, client):
        """Update email returns updated user."""
        signup = client.post(
            "/api/v1/auth/signup",
            json={"email": "oldemail@test.com", "username": "emailuser", "password": "password123"},
        )
        auth_token = signup.json()["auth_token"]
        user_id = signup.json()["user"]["id"]
        response = client.patch(
            f"/api/v1/auth/users/{user_id}/email",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"email": "newemail@test.com"},
        )
        assert response.status_code == 200
        assert response.json()["email"] == "newemail@test.com"

    def test_refresh_returns_401_for_invalid_token(self, client):
        """Refresh with invalid token returns 401."""
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid-token"},
        )
        assert response.status_code == 401

    def test_get_user_returns_403_for_other_user(self, client):
        """Get user returns 403 when requesting another user's data."""
        signup = client.post(
            "/api/v1/auth/signup",
            json={"email": "owner@test.com", "username": "owner", "password": "password123"},
        )
        auth_token = signup.json()["auth_token"]
        other_id = "660e8400-e29b-41d4-a716-446655440001"
        response = client.get(
            f"/api/v1/auth/users/{other_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 403

    def test_get_user_returns_404_for_nonexistent(self, client_with_auth_bypass):
        """Get user returns 404 when user does not exist (auth bypass, no signup)."""
        response = client_with_auth_bypass.get(
            "/api/v1/auth/users/550e8400-e29b-41d4-a716-446655440000"
        )
        assert response.status_code == 404

    def test_signup_returns_409_for_duplicate_email(self, client):
        """Signup with existing email returns 409."""
        client.post(
            "/api/v1/auth/signup",
            json={"email": "signup-dup@test.com", "username": "user1", "password": "password123"},
        )
        r = client.post(
            "/api/v1/auth/signup",
            json={"email": "signup-dup@test.com", "username": "user2", "password": "otherpass123"},
        )
        assert r.status_code == 409
        assert "email" in r.json()["detail"].lower()

    def test_update_email_returns_409_for_duplicate(self, client):
        """Update email to existing email returns 409."""
        client.post(
            "/api/v1/auth/signup",
            json={"email": "email-dup-first@test.com", "username": "first", "password": "password123"},
        )
        r2 = client.post(
            "/api/v1/auth/signup",
            json={"email": "email-dup-second@test.com", "username": "second", "password": "password123"},
        )
        auth_token = r2.json()["auth_token"]
        user_id = r2.json()["user"]["id"]
        r = client.patch(
            f"/api/v1/auth/users/{user_id}/email",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"email": "email-dup-first@test.com"},
        )
        assert r.status_code == 409

    def test_update_password_returns_404_for_nonexistent(self, client_with_auth_bypass):
        """Update password returns 404 when user does not exist."""
        r = client_with_auth_bypass.patch(
            "/api/v1/auth/users/550e8400-e29b-41d4-a716-446655440000/password",
            json={"password": "newpass123"},
        )
        assert r.status_code == 404

    def test_delete_user_returns_404_for_nonexistent(self, client_with_auth_bypass):
        """Delete user returns 404 when user does not exist."""
        r = client_with_auth_bypass.delete(
            "/api/v1/auth/users/550e8400-e29b-41d4-a716-446655440000"
        )
        assert r.status_code == 404


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
        assert data["owner_subject"] == "user:550e8400-e29b-41d4-a716-446655440000"

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

    def test_list_chats_shared_with_me(self, client_with_auth_bypass):
        """Owner sees no shared-with-me rows; grantee sees shared chats flat."""
        from src.auth.utils.jwt import SubjectPayload, SubjectType
        from src.server.app import app
        from src.server.dependencies import get_current_subject

        grantee_id = "660e8400-e29b-41d4-a716-446655440001"
        grantee_payload = SubjectPayload(
            subject_type=SubjectType.USER,
            subject_id=grantee_id,
        )

        r0 = client_with_auth_bypass.get("/api/v1/chats/shared-with-me")
        assert r0.status_code == 200
        assert r0.json()["items"] == []

        r1 = client_with_auth_bypass.post("/api/v1/chats", json={})
        assert r1.status_code == 200
        chat_id = r1.json()["id"]
        r2 = client_with_auth_bypass.post(
            f"/api/v1/chats/{chat_id}/shares",
            json={
                "subject_type": "user",
                "subject_id": grantee_id,
                "role": "viewer",
            },
        )
        assert r2.status_code == 200

        app.dependency_overrides[get_current_subject] = lambda: grantee_payload
        r3 = client_with_auth_bypass.get("/api/v1/chats/shared-with-me")
        assert r3.status_code == 200
        items = r3.json()["items"]
        assert len(items) == 1
        assert items[0]["id"] == chat_id

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
        assert r2.json()["subject"] == f"user:{grantee_id}"
        assert r2.json()["role"] == "viewer"
        # List shares
        r3 = client_with_auth_bypass.get(f"/api/v1/chats/{chat_id}/shares")
        assert r3.status_code == 200
        shares = r3.json()
        assert len(shares) == 1
        assert shares[0]["subject"] == f"user:{grantee_id}"
        # Remove share (new path: /chats/{id}/shares/{subject_type}/{subject_id})
        r4 = client_with_auth_bypass.delete(
            f"/api/v1/chats/{chat_id}/shares/user/{grantee_id}"
        )
        assert r4.status_code == 204
        r5 = client_with_auth_bypass.get(f"/api/v1/chats/{chat_id}/shares")
        assert r5.status_code == 200
        assert len(r5.json()) == 0

    def test_add_share_to_self_returns_400(self, client_with_auth_bypass):
        """Cannot add a share grantee that is the same as the current user."""
        r1 = client_with_auth_bypass.post("/api/v1/chats", json={})
        assert r1.status_code == 200
        chat_id = r1.json()["id"]
        # Same subject_id as MOCK_SUBJECT in conftest (token user)
        r2 = client_with_auth_bypass.post(
            f"/api/v1/chats/{chat_id}/shares",
            json={
                "subject_type": "user",
                "subject_id": "550e8400-e29b-41d4-a716-446655440000",
                "role": "viewer",
            },
        )
        assert r2.status_code == 400
        assert "yourself" in r2.json()["detail"].lower()

    def test_get_folder(self, client_with_auth_bypass):
        """Get folder returns folder by id."""
        r1 = client_with_auth_bypass.post(
            "/api/v1/folders", json={"name": "Get Folder"}
        )
        assert r1.status_code == 200
        folder_id = r1.json()["id"]
        r2 = client_with_auth_bypass.get(f"/api/v1/folders/{folder_id}")
        assert r2.status_code == 200
        assert r2.json()["name"] == "Get Folder"

    def test_patch_folder_name_and_system_prompt(self, client_with_auth_bypass):
        """Patch folder updates name and system_prompt."""
        r1 = client_with_auth_bypass.post(
            "/api/v1/folders", json={"name": "Original"}
        )
        assert r1.status_code == 200
        folder_id = r1.json()["id"]
        r2 = client_with_auth_bypass.patch(
            f"/api/v1/folders/{folder_id}",
            json={"name": "Renamed", "system_prompt": "You are helpful."},
        )
        assert r2.status_code == 200
        assert r2.json()["name"] == "Renamed"
        assert r2.json()["system_prompt"] == "You are helpful."

    def test_add_message_with_reply(self, client_with_mock_agent):
        """Add message with generate_reply returns message and AI reply."""
        r1 = client_with_mock_agent.post("/api/v1/chats", json={})
        assert r1.status_code == 200
        chat_id = r1.json()["id"]
        r2 = client_with_mock_agent.post(
            f"/api/v1/chats/{chat_id}/messages",
            json={"role": "user", "content": "Hello", "generate_reply": True},
        )
        assert r2.status_code == 200
        data = r2.json()
        assert "message" in data
        assert data["message"]["role"] == "user"
        assert data["message"]["content"] == "Hello"
        assert "reply" in data
        assert data["reply"] == "Mocked reply"

    def test_add_message_auto_names_chat_from_first_message(
        self, client_with_auth_bypass
    ):
        """First user message sets chat title to first 30 chars."""
        r1 = client_with_auth_bypass.post("/api/v1/chats", json={})
        assert r1.status_code == 200
        chat_id = r1.json()["id"]
        assert r1.json().get("title") is None or r1.json().get("title") == ""
        first_msg = "What is the capital of France and why is it significant?"
        r2 = client_with_auth_bypass.post(
            f"/api/v1/chats/{chat_id}/messages",
            json={"role": "user", "content": first_msg, "generate_reply": False},
        )
        assert r2.status_code == 200
        r3 = client_with_auth_bypass.get(f"/api/v1/chats/{chat_id}")
        assert r3.status_code == 200
        # Title is first 30 chars of message; adapter may strip when storing
        expected_title = first_msg.strip()[:30].strip()
        assert r3.json()["title"] == expected_title

    def test_update_chat_400_when_no_fields(self, client_with_auth_bypass):
        """PATCH chat with empty body returns 400."""
        r1 = client_with_auth_bypass.post("/api/v1/chats", json={})
        assert r1.status_code == 200
        chat_id = r1.json()["id"]
        r2 = client_with_auth_bypass.patch(
            f"/api/v1/chats/{chat_id}",
            json={},
        )
        assert r2.status_code == 400
        assert "title" in r2.json()["detail"].lower() or "folder" in r2.json()["detail"].lower()

    def test_update_chat_404_for_unknown(self, client_with_auth_bypass):
        """PATCH chat returns 404 for unknown chat."""
        r = client_with_auth_bypass.patch(
            "/api/v1/chats/550e8400-e29b-41d4-a716-446655440099",
            json={"title": "New Title"},
        )
        assert r.status_code == 404

    def test_add_message_rejects_non_user_role(self, client_with_auth_bypass):
        """POST message with role!=user returns 400."""
        r1 = client_with_auth_bypass.post("/api/v1/chats", json={})
        assert r1.status_code == 200
        chat_id = r1.json()["id"]
        r2 = client_with_auth_bypass.post(
            f"/api/v1/chats/{chat_id}/messages",
            json={"role": "assistant", "content": "Hi", "generate_reply": False},
        )
        assert r2.status_code == 400

    def test_add_message_403_for_unknown_chat(self, client_with_auth_bypass):
        """POST message to unknown chat returns 403 (no access)."""
        r = client_with_auth_bypass.post(
            "/api/v1/chats/550e8400-e29b-41d4-a716-446655440099/messages",
            json={"role": "user", "content": "Hi", "generate_reply": False},
        )
        assert r.status_code == 403

    def test_get_messages_404_for_unknown_chat(self, client_with_auth_bypass):
        """GET messages returns 404 for unknown chat."""
        r = client_with_auth_bypass.get(
            "/api/v1/chats/550e8400-e29b-41d4-a716-446655440099/messages"
        )
        assert r.status_code == 404

    def test_delete_folder_404_for_unknown(self, client_with_auth_bypass):
        """DELETE folder returns 404 for unknown folder."""
        r = client_with_auth_bypass.delete(
            "/api/v1/folders/550e8400-e29b-41d4-a716-446655440099"
        )
        assert r.status_code == 404

    def test_get_folder_404_for_unknown(self, client_with_auth_bypass):
        """GET folder returns 404 for unknown folder."""
        r = client_with_auth_bypass.get(
            "/api/v1/folders/550e8400-e29b-41d4-a716-446655440099"
        )
        assert r.status_code == 404

    def test_move_chat_to_folder_404_for_unknown(self, client_with_auth_bypass):
        """PATCH chat folder returns 404 for unknown chat."""
        r = client_with_auth_bypass.patch(
            "/api/v1/chats/550e8400-e29b-41d4-a716-446655440099/folder",
            json={"folder_id": None},
        )
        assert r.status_code == 404

    def test_list_shares_404_for_unknown_chat(self, client_with_auth_bypass):
        """GET shares returns 404 for unknown chat."""
        r = client_with_auth_bypass.get(
            "/api/v1/chats/550e8400-e29b-41d4-a716-446655440099/shares"
        )
        assert r.status_code == 404

    def test_remove_share_404_for_nonexistent(self, client_with_auth_bypass):
        """DELETE share returns 404 when share does not exist."""
        r1 = client_with_auth_bypass.post("/api/v1/chats", json={})
        assert r1.status_code == 200
        chat_id = r1.json()["id"]
        r2 = client_with_auth_bypass.delete(
            f"/api/v1/chats/{chat_id}/shares/user/660e8400-e29b-41d4-a716-446655440001"
        )
        assert r2.status_code == 404
