"""Auth adapter factory: creates the correct adapter based on settings."""

from __future__ import annotations

import asyncpg

from src.auth.adapters.mock.mock_auth_adapter import MockAuthAdapter
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

    provider = settings.AUTHENTICATION_SERVICE_PROVIDER.lower()

    if provider == "mock":
        return MockAuthAdapter(), None

    if provider == "sql":
        dsn = settings.authentication_service_database_url()
        if dsn is None:
            raise ValueError(
                "AUTHENTICATION_SERVICE_PROVIDER=sql requires AUTHENTICATION_SERVICE_USERNAME, "
                "AUTHENTICATION_SERVICE_PASSWORD, and APP_DATA_DATABASE_HOST / APP_DATA_DATABASE_NAME"
            )
        pool = await asyncpg.create_pool(
            dsn,
            min_size=1,
            max_size=10,
            command_timeout=60,
        )
        adapter: AuthPort = PostgresAuthAdapter(pool)
        return adapter, pool

    if provider == "supabase":
        if (
            not settings.AUTHENTICATION_SERVICE_URL.strip()
            or settings.AUTHENTICATION_SERVICE_PASSWORD is None
        ):
            raise ValueError(
                "AUTHENTICATION_SERVICE_PROVIDER=supabase requires AUTHENTICATION_SERVICE_URL and "
                "AUTHENTICATION_SERVICE_PASSWORD (service role secret)"
            )
        supabase_pool: asyncpg.Pool | None = None
        if settings.AUTHENTICATION_SERVICE_DATABASE_URL is not None:
            supabase_pool = await asyncpg.create_pool(
                settings.AUTHENTICATION_SERVICE_DATABASE_URL.get_secret_value(),
                min_size=1,
                max_size=5,
                command_timeout=60,
            )
        adapter = SupabaseAuthAdapter(
            supabase_url=settings.AUTHENTICATION_SERVICE_URL.strip(),
            service_role_key=settings.AUTHENTICATION_SERVICE_PASSWORD.get_secret_value(),
            database_pool=supabase_pool,
        )
        return adapter, supabase_pool

    raise ValueError(
        f"Unknown AUTHENTICATION_SERVICE_PROVIDER: {settings.AUTHENTICATION_SERVICE_PROVIDER}. "
        "Use 'sql', 'supabase', or 'mock' (for tests)."
    )
