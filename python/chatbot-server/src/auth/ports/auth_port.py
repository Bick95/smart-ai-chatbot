"""Auth port (interface) for the hexagonal architecture.

Implementations must hash passwords before storing them to enforce 0-trust
with any underlying provider.
"""

from __future__ import annotations

from typing import Protocol

from src.auth.ports.types import AuthUser


class AuthPort(Protocol):
    """Port for authentication operations.

    All adapters must hash passwords before persisting them.
    """

    async def signup(self, email: str, username: str, password: str) -> AuthUser:
        """Create a new user. Password is hashed before storage."""
        ...

    async def delete_account(self, user_id: str) -> bool:
        """Delete a user account. Returns True if deleted."""
        ...

    async def update_username(self, user_id: str, new_username: str) -> bool:
        """Update a user's username. Returns True if updated."""
        ...

    async def update_email(self, user_id: str, new_email: str) -> bool:
        """Update a user's email. Returns True if updated. Raises ValueError if email already in use."""
        ...

    async def update_password(self, user_id: str, new_password: str) -> bool:
        """Update a user's password. Password is hashed before storage."""
        ...

    async def get_user_by_id(self, user_id: str) -> AuthUser | None:
        """Fetch a user by ID. Returns None if not found."""
        ...

    async def get_user_by_email(self, email: str) -> AuthUser | None:
        """Fetch a user by email. Returns None if not found.

        Note: For Supabase without SUPABASE_DATABASE_URL, this fetches all users
        via list_users (inefficient). Set SUPABASE_DATABASE_URL for efficient
        direct query on auth.users. Prefer get_user_by_id or verify_credentials
        when possible.
        """
        ...

    async def verify_credentials(self, email: str, password: str) -> AuthUser | None:
        """Verify email and password. Returns user if valid, None otherwise."""
        ...
