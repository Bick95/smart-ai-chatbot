"""App data adapter factory: creates the correct adapter based on settings."""

from __future__ import annotations

import asyncpg

from src.app_data.adapters.mock.mock_chat_adapter import MockChatAdapter
from src.app_data.adapters.postgres.postgres_chat_adapter import (
    PostgresChatAdapter,
)
from src.app_data.ports.chat_port import ChatPort
from src.settings import settings


async def _get_app_data_pool(
    existing_pool: asyncpg.Pool | None,
) -> tuple[asyncpg.Pool, bool]:
    """Get pool for app data. Returns (pool, owns_pool).
    If existing_pool is provided, use it. Otherwise create from config.
    """
    if existing_pool is not None:
        return existing_pool, False
    url = None
    if settings.APP_DATA_DATABASE_URL is not None:
        url = settings.APP_DATA_DATABASE_URL.get_secret_value()
    elif settings.DATABASE_URL is not None:
        url = settings.DATABASE_URL.get_secret_value()
    elif settings.SUPABASE_DATABASE_URL is not None:
        url = settings.SUPABASE_DATABASE_URL.get_secret_value()
    if url is None:
        raise ValueError(
            "APP_DATA_PROVIDER=postgres requires a database URL. "
            "Set APP_DATA_DATABASE_URL, DATABASE_URL, or SUPABASE_DATABASE_URL."
        )
    pool = await asyncpg.create_pool(
        url,
        min_size=1,
        max_size=10,
        command_timeout=60,
    )
    return pool, True


async def create_chat_adapter(
    existing_pool: asyncpg.Pool | None = None,
) -> tuple[ChatPort, asyncpg.Pool | None]:
    """Create chat adapter.

    Args:
        existing_pool: Pool from auth (when auth uses postgres or supabase with DB).
            When provided, migrations are run on it and it is reused.

    Returns:
        (adapter, pool_to_close) - pool_to_close is the pool to close on shutdown
        if we created it; None if we reuse existing_pool or use mock.
    """
    provider = settings.APP_DATA_PROVIDER.lower()

    if provider == "mock":
        return MockChatAdapter(), None

    if provider == "postgres":
        pool, owns_pool = await _get_app_data_pool(existing_pool)
        adapter: ChatPort = PostgresChatAdapter(pool)
        return adapter, pool if owns_pool else None

    raise ValueError(
        f"Unknown APP_DATA_PROVIDER: {settings.APP_DATA_PROVIDER}. "
        "Use 'postgres' or 'mock'."
    )
