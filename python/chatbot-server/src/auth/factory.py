"""Auth adapter factory: creates the correct adapter based on settings."""

from __future__ import annotations

import asyncpg

from src.auth.adapters.postgres.migrations import run_migrations
from src.auth.adapters.postgres.postgres_auth_adapter import PostgresAuthAdapter
from src.auth.adapters.supabase.supabase_auth_adapter import SupabaseAuthAdapter
from src.auth.ports.auth_port import AuthPort
from src.settings import settings


async def create_auth_adapter() -> tuple[AuthPort, object | None]:
    """Create auth adapter. Call only when AUTH_ENABLED=True."""
    """Create the auth adapter and optional cleanup object.

    Returns (adapter, cleanup) where cleanup is a callable/object to close
    resources on shutdown (e.g. pool.close), or None.
    """
    provider = settings.AUTH_PROVIDER.lower()

    if provider == "postgres":
        if settings.DATABASE_URL is None:
            raise ValueError(
                "AUTH_PROVIDER=postgres requires DATABASE_URL to be set"
            )
        pool = await asyncpg.create_pool(
            settings.DATABASE_URL.get_secret_value(),
            min_size=1,
            max_size=10,
            command_timeout=60,
        )
        await run_migrations(pool)
        adapter: AuthPort = PostgresAuthAdapter(pool)
        return adapter, pool

    if provider == "supabase":
        if not settings.SUPABASE_URL or settings.SUPABASE_SERVICE_ROLE_KEY is None:
            raise ValueError(
                "AUTH_PROVIDER=supabase requires SUPABASE_URL and "
                "SUPABASE_SERVICE_ROLE_KEY to be set"
            )
        adapter = SupabaseAuthAdapter(
            supabase_url=settings.SUPABASE_URL,
            service_role_key=settings.SUPABASE_SERVICE_ROLE_KEY.get_secret_value(),
        )
        return adapter, None

    raise ValueError(
        f"Unknown AUTH_PROVIDER: {settings.AUTH_PROVIDER}. "
        "Use 'postgres' or 'supabase'."
    )
