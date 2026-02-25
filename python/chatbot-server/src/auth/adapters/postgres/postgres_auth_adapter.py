"""Postgres auth adapter: stores users in a standalone Postgres database."""

from __future__ import annotations

from uuid import uuid4

import asyncpg

from src.auth.ports.types import AuthUser
from src.auth.utils.password import hash_password, verify_password


class PostgresAuthAdapter:
    """Auth adapter using a plain Postgres database.

    Passwords are hashed before storage (0-trust).
    """

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def signup(self, email: str, username: str, password: str) -> AuthUser:
        password_hash = hash_password(password)
        user_id = str(uuid4())
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO auth_users (id, email, username, password_hash, updated_at)
                VALUES ($1, $2, $3, $4, NOW())
                """,
                user_id,
                email.lower().strip(),
                username.strip(),
                password_hash,
            )
        return AuthUser(id=user_id, email=email.lower().strip(), username=username.strip())

    async def delete_account(self, user_id: str) -> bool:
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM auth_users WHERE id = $1",
                user_id,
            )
        return result == "DELETE 1"

    async def update_username(self, user_id: str, new_username: str) -> bool:
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                """
                UPDATE auth_users
                SET username = $1, updated_at = NOW()
                WHERE id = $2
                """,
                new_username.strip(),
                user_id,
            )
        return result == "UPDATE 1"

    async def update_password(self, user_id: str, new_password: str) -> bool:
        password_hash = hash_password(new_password)
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                """
                UPDATE auth_users
                SET password_hash = $1, updated_at = NOW()
                WHERE id = $2
                """,
                password_hash,
                user_id,
            )
        return result == "UPDATE 1"

    async def get_user_by_id(self, user_id: str) -> AuthUser | None:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, email, username FROM auth_users WHERE id = $1",
                user_id,
            )
        if row is None:
            return None
        return AuthUser(id=str(row["id"]), email=row["email"], username=row["username"])

    async def get_user_by_email(self, email: str) -> AuthUser | None:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, email, username FROM auth_users WHERE email = $1",
                email.lower().strip(),
            )
        if row is None:
            return None
        return AuthUser(id=str(row["id"]), email=row["email"], username=row["username"])

    async def verify_credentials(self, email: str, password: str) -> AuthUser | None:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, email, username, password_hash FROM auth_users WHERE email = $1",
                email.lower().strip(),
            )
        if row is None:
            return None
        if not verify_password(password, row["password_hash"]):
            return None
        return AuthUser(id=str(row["id"]), email=row["email"], username=row["username"])
