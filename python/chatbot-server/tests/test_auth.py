"""Tests for auth adapters and auth-related logic."""

import pytest

from src.auth.adapters.mock.mock_auth_adapter import MockAuthAdapter


@pytest.mark.unit
class TestMockAuthAdapter:
    """Direct unit tests for MockAuthAdapter to catch regressions."""

    @pytest.fixture
    def adapter(self) -> MockAuthAdapter:
        return MockAuthAdapter()

    @pytest.mark.asyncio
    async def test_signup_creates_user(self, adapter: MockAuthAdapter):
        """Signup creates user with correct email, username, id."""
        user = await adapter.signup(
            email="alice@example.com",
            username="alice",
            password="securepass123",
        )
        assert user.email == "alice@example.com"
        assert user.username == "alice"
        assert user.id
        assert len(user.id) == 36  # UUID format

    @pytest.mark.asyncio
    async def test_signup_normalizes_email_to_lowercase(self, adapter: MockAuthAdapter):
        """Signup stores email in lowercase."""
        user = await adapter.signup(
            email="Alice@Example.COM",
            username="alice",
            password="securepass123",
        )
        assert user.email == "alice@example.com"

    @pytest.mark.asyncio
    async def test_signup_rejects_duplicate_email(self, adapter: MockAuthAdapter):
        """Signup raises ValueError when email already registered."""
        await adapter.signup(
            email="dup@example.com",
            username="user1",
            password="password123",
        )
        with pytest.raises(ValueError, match="Email already registered"):
            await adapter.signup(
                email="dup@example.com",
                username="user2",
                password="otherpass123",
            )

    @pytest.mark.asyncio
    async def test_signup_rejects_duplicate_email_case_insensitive(
        self, adapter: MockAuthAdapter
    ):
        """Duplicate email check is case-insensitive."""
        await adapter.signup(
            email="same@example.com",
            username="user1",
            password="password123",
        )
        with pytest.raises(ValueError, match="Email already registered"):
            await adapter.signup(
                email="SAME@EXAMPLE.COM",
                username="user2",
                password="otherpass123",
            )

    @pytest.mark.asyncio
    async def test_verify_credentials_returns_user_on_valid(
        self, adapter: MockAuthAdapter
    ):
        """verify_credentials returns user when email and password match."""
        await adapter.signup(
            email="valid@example.com",
            username="validuser",
            password="mypassword123",
        )
        user = await adapter.verify_credentials("valid@example.com", "mypassword123")
        assert user is not None
        assert user.email == "valid@example.com"
        assert user.username == "validuser"

    @pytest.mark.asyncio
    async def test_verify_credentials_returns_none_on_wrong_password(
        self, adapter: MockAuthAdapter
    ):
        """verify_credentials returns None when password is wrong."""
        await adapter.signup(
            email="user@example.com",
            username="user",
            password="correctpass123",
        )
        user = await adapter.verify_credentials("user@example.com", "wrongpassword")
        assert user is None

    @pytest.mark.asyncio
    async def test_verify_credentials_returns_none_on_unknown_email(
        self, adapter: MockAuthAdapter
    ):
        """verify_credentials returns None when email not found."""
        user = await adapter.verify_credentials("unknown@example.com", "anypass123")
        assert user is None

    @pytest.mark.asyncio
    async def test_get_user_by_email_returns_user(self, adapter: MockAuthAdapter):
        """get_user_by_email returns user when found."""
        created = await adapter.signup(
            email="lookup@example.com",
            username="lookup",
            password="pass123",
        )
        found = await adapter.get_user_by_email("lookup@example.com")
        assert found is not None
        assert found.id == created.id
        assert found.email == created.email

    @pytest.mark.asyncio
    async def test_get_user_by_id_returns_user(self, adapter: MockAuthAdapter):
        """get_user_by_id returns user when found."""
        created = await adapter.signup(
            email="idlookup@example.com",
            username="idlookup",
            password="pass123",
        )
        found = await adapter.get_user_by_id(created.id)
        assert found is not None
        assert found.id == created.id

    @pytest.mark.asyncio
    async def test_get_user_by_id_returns_none_for_unknown(self, adapter: MockAuthAdapter):
        """get_user_by_id returns None when not found."""
        found = await adapter.get_user_by_id("550e8400-e29b-41d4-a716-446655440000")
        assert found is None

    @pytest.mark.asyncio
    async def test_update_username(self, adapter: MockAuthAdapter):
        """update_username changes username."""
        user = await adapter.signup(
            email="update@example.com",
            username="oldname",
            password="pass123",
        )
        ok = await adapter.update_username(user.id, "newname")
        assert ok is True
        found = await adapter.get_user_by_id(user.id)
        assert found is not None
        assert found.username == "newname"
        assert found.email == "update@example.com"

    @pytest.mark.asyncio
    async def test_update_email(self, adapter: MockAuthAdapter):
        """update_email changes email."""
        user = await adapter.signup(
            email="old@example.com",
            username="user",
            password="pass123",
        )
        ok = await adapter.update_email(user.id, "new@example.com")
        assert ok is True
        found = await adapter.get_user_by_email("new@example.com")
        assert found is not None
        assert found.id == user.id

    @pytest.mark.asyncio
    async def test_update_email_rejects_duplicate(self, adapter: MockAuthAdapter):
        """update_email raises ValueError when new email already in use."""
        await adapter.signup(
            email="first@example.com",
            username="first",
            password="pass123",
        )
        user2 = await adapter.signup(
            email="second@example.com",
            username="second",
            password="pass123",
        )
        with pytest.raises(ValueError, match="Email already registered"):
            await adapter.update_email(user2.id, "first@example.com")

    @pytest.mark.asyncio
    async def test_update_password(self, adapter: MockAuthAdapter):
        """update_password allows login with new password."""
        user = await adapter.signup(
            email="pwd@example.com",
            username="pwduser",
            password="oldpass123",
        )
        ok = await adapter.update_password(user.id, "newpass456")
        assert ok is True
        assert await adapter.verify_credentials("pwd@example.com", "oldpass123") is None
        assert await adapter.verify_credentials("pwd@example.com", "newpass456") is not None

    @pytest.mark.asyncio
    async def test_delete_account(self, adapter: MockAuthAdapter):
        """delete_account removes user."""
        user = await adapter.signup(
            email="delete@example.com",
            username="todelete",
            password="pass123",
        )
        ok = await adapter.delete_account(user.id)
        assert ok is True
        assert await adapter.get_user_by_id(user.id) is None
        assert await adapter.get_user_by_email("delete@example.com") is None

    @pytest.mark.asyncio
    async def test_search_users_by_username(self, adapter: MockAuthAdapter):
        """search_users_by_username returns matching users."""
        await adapter.signup("a@x.com", "alice", "pass123")
        await adapter.signup("b@x.com", "bob", "pass123")
        await adapter.signup("c@x.com", "charlie", "pass123")
        matches = await adapter.search_users_by_username("al", limit=10)
        assert len(matches) == 1
        assert matches[0].username == "alice"
        matches = await adapter.search_users_by_username("e", limit=10)
        assert len(matches) == 2  # alice, charlie
        assert {u.username for u in matches} == {"alice", "charlie"}
