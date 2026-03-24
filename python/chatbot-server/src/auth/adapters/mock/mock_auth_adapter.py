"""In-memory mock auth adapter for testing (no DB required)."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from src.auth.ports.types import AuthUser
from src.auth.utils.password import hash_password, verify_password


class MockAuthAdapter:
    """In-memory auth adapter for tests. Implements AuthPort."""

    def __init__(self) -> None:
        self._users: dict[str, _StoredUser] = {}

    async def signup(self, email: str, username: str, password: str) -> AuthUser:
        email_lower = email.lower().strip()
        for u in self._users.values():
            if u.user.email == email_lower:
                raise ValueError("Email already registered")
        user_id = str(uuid4())
        user = AuthUser(
            id=user_id,
            email=email_lower,
            username=username.strip(),
            created_at=datetime.now(timezone.utc),
        )
        self._users[user_id] = _StoredUser(
            user=user,
            password_hash=hash_password(password),
        )
        return user

    async def delete_account(self, user_id: str) -> bool:
        if user_id in self._users:
            del self._users[user_id]
            return True
        return False

    async def update_username(self, user_id: str, new_username: str) -> bool:
        if user_id not in self._users:
            return False
        stored = self._users[user_id]
        self._users[user_id] = _StoredUser(
            user=AuthUser(
                id=stored.user.id,
                email=stored.user.email,
                username=new_username.strip(),
                created_at=stored.user.created_at,
            ),
            password_hash=stored.password_hash,
        )
        return True

    async def update_email(self, user_id: str, new_email: str) -> bool:
        if user_id not in self._users:
            return False
        email_lower = new_email.lower().strip()
        for uid, u in self._users.items():
            if uid != user_id and u.user.email == email_lower:
                raise ValueError("Email already registered")
        stored = self._users[user_id]
        self._users[user_id] = _StoredUser(
            user=AuthUser(
                id=stored.user.id,
                email=email_lower,
                username=stored.user.username,
                created_at=stored.user.created_at,
            ),
            password_hash=stored.password_hash,
        )
        return True

    async def update_password(self, user_id: str, new_password: str) -> bool:
        if user_id not in self._users:
            return False
        stored = self._users[user_id]
        self._users[user_id] = _StoredUser(
            user=stored.user,
            password_hash=hash_password(new_password),
        )
        return True

    async def get_user_by_id(self, user_id: str) -> AuthUser | None:
        stored = self._users.get(user_id)
        return stored.user if stored else None

    async def get_user_by_email(self, email: str) -> AuthUser | None:
        email_lower = email.lower()
        for stored in self._users.values():
            if stored.user.email == email_lower:
                return stored.user
        return None

    async def verify_credentials(self, email: str, password: str) -> AuthUser | None:
        user = await self.get_user_by_email(email)
        if user is None:
            return None
        stored = self._users[user.id]
        if not verify_password(password, stored.password_hash):
            return None
        return user

    async def search_users_by_username(
        self, query: str, limit: int = 10
    ) -> list[AuthUser]:
        q = query.strip().lower()
        if not q:
            return []
        matches = [u.user for u in self._users.values() if q in u.user.username.lower()]
        matches.sort(key=lambda u: u.username)
        return matches[:limit]


class _StoredUser:
    def __init__(self, user: AuthUser, password_hash: str) -> None:
        self.user = user
        self.password_hash = password_hash
