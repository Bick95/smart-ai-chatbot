"""Supabase auth adapter: wraps Supabase Auth with password hashing (0-trust)."""

from __future__ import annotations

import asyncio

from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions

from src.auth.ports.types import AuthUser
from src.auth.utils.password import hash_password


class SupabaseAuthAdapter:
    """Auth adapter wrapping Supabase Auth.

    Passwords are hashed before passing to Supabase (0-trust).
    Supabase will hash again; we pass our hash as the 'password' so that
    stored value is hash(hash(plain)). For sign_in we hash(plain) and pass
    that; Supabase hashes and compares.
    """

    def __init__(self, supabase_url: str, service_role_key: str) -> None:
        self._client: Client = create_client(
            supabase_url,
            service_role_key,
            options=ClientOptions(
                auto_refresh_token=False,
                persist_session=False,
            ),
        )

    async def signup(self, email: str, username: str, password: str) -> AuthUser:
        hashed = hash_password(password)

        def _create() -> AuthUser:
            response = self._client.auth.admin.create_user(
                {
                    "email": email.lower().strip(),
                    "password": hashed,
                    "email_confirm": True,
                    "user_metadata": {"username": username.strip()},
                }
            )
            if response.user is None:
                raise ValueError("Supabase create_user returned no user")
            user = response.user
            return AuthUser(
                id=str(user.id),
                email=user.email or email,
                username=user.user_metadata.get("username", username.strip()),
            )

        return await asyncio.to_thread(_create)

    async def delete_account(self, user_id: str) -> bool:
        await asyncio.to_thread(self._client.auth.admin.delete_user, user_id)
        return True

    async def update_username(self, user_id: str, new_username: str) -> bool:
        def _update() -> None:
            self._client.auth.admin.update_user_by_id(
                user_id,
                {"user_metadata": {"username": new_username.strip()}},
            )

        await asyncio.to_thread(_update)
        return True

    async def update_password(self, user_id: str, new_password: str) -> bool:
        hashed = hash_password(new_password)

        def _update() -> None:
            self._client.auth.admin.update_user_by_id(user_id, {"password": hashed})

        await asyncio.to_thread(_update)
        return True

    async def get_user_by_id(self, user_id: str) -> AuthUser | None:
        def _get() -> AuthUser | None:
            response = self._client.auth.admin.get_user_by_id(user_id)
            if response.user is None:
                return None
            user = response.user
            return AuthUser(
                id=str(user.id),
                email=user.email or "",
                username=user.user_metadata.get("username", ""),
            )

        return await asyncio.to_thread(_get)

    async def get_user_by_email(self, email: str) -> AuthUser | None:
        def _get() -> AuthUser | None:
            response = self._client.auth.admin.list_users()
            users = getattr(response, "users", []) or []
            for u in users:
                u_email: str | None = getattr(u, "email", None)
                if u_email and u_email.lower() == email.lower().strip():
                    u_meta = getattr(u, "user_metadata", {}) or {}
                    u_username = u_meta.get("username", "") if isinstance(u_meta, dict) else ""
                    return AuthUser(id=str(u.id), email=u_email, username=u_username)
            return None

        return await asyncio.to_thread(_get)

    async def verify_credentials(self, email: str, password: str) -> AuthUser | None:
        hashed = hash_password(password)

        def _verify() -> AuthUser | None:
            response = self._client.auth.sign_in_with_password(
                {"email": email.lower().strip(), "password": hashed}
            )
            if response.user is None:
                return None
            user = response.user
            return AuthUser(
                id=str(user.id),
                email=user.email or email,
                username=user.user_metadata.get("username", ""),
            )

        return await asyncio.to_thread(_verify)
