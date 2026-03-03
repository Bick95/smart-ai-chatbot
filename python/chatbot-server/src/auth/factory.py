"""Auth adapter factory: creates the correct adapter based on settings."""

from __future__ import annotations

import asyncpg

from src.auth.adapters.mock.mock_auth_adapter import MockAuthAdapter
from src.auth.adapters.postgres.migrations import run_migrations
from src.auth.adapters.postgres.postgres_auth_adapter import PostgresAuthAdapter
from src.auth.adapters.supabase.supabase_auth_adapter import SupabaseAuthAdapter
from src.auth.ports.auth_port import AuthPort
from src.settings import settings


async def create_auth_adapter() -> tuple[AuthPort, asyncpg.Pool | None]:
    """Create auth adapter. Auth is mandatory.

    Returns (adapter, pool) where pool is an asyncpg.Pool to close on shutdown,
    or None (mock adapter or Supabase without direct DB).
    """
    if settings.JWT_SECRET_KEY is None:
        raise ValueError("JWT_SECRET_KEY is required")

    provider = settings.AUTH_PROVIDER.lower()

    if provider == "mock":
        return MockAuthAdapter(), None

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
        pool: asyncpg.Pool | None = None
        if settings.SUPABASE_DATABASE_URL is not None:
            pool = await asyncpg.create_pool(
                settings.SUPABASE_DATABASE_URL.get_secret_value(),
                min_size=1,
                max_size=5,
                command_timeout=60,
            )
        adapter = SupabaseAuthAdapter(
            supabase_url=settings.SUPABASE_URL,
            service_role_key=settings.SUPABASE_SERVICE_ROLE_KEY.get_secret_value(),
            database_pool=pool,
        )
        return adapter, pool

    raise ValueError(
        f"Unknown AUTH_PROVIDER: {settings.AUTH_PROVIDER}. "
        "Use 'postgres', 'supabase', or 'mock' (for tests)."
    )
