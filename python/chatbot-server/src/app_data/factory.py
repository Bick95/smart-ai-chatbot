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

    If existing_pool is provided and matches the configured app DSN, use it.
    Otherwise create a new pool from APP_DATA_DATABASE_*.
    """
    dsn = settings.app_data_database_url()
    if dsn is None:
        raise ValueError(
            "APP_DATA_DATABASE_PROVIDER=sql requires APP_DATA_DATABASE_USERNAME, "
            "APP_DATA_DATABASE_PASSWORD, and APP_DATA_DATABASE_HOST / APP_DATA_DATABASE_NAME"
        )
    if existing_pool is not None:
        return existing_pool, False
    pool = await asyncpg.create_pool(
        dsn,
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
        existing_pool: Pool from auth when connection parameters match app data (same DSN).

    Returns:
        (adapter, pool_to_close) — pool_to_close is the pool this factory created, if any;
        None if we reused existing_pool or use mock.
    """
    provider = settings.APP_DATA_DATABASE_PROVIDER.lower()

    if provider == "mock":
        return MockChatAdapter(), None

    if provider == "sql":
        pool, owns_pool = await _get_app_data_pool(existing_pool)
        adapter: ChatPort = PostgresChatAdapter(pool)
        return adapter, pool if owns_pool else None

    raise ValueError(
        f"Unknown APP_DATA_DATABASE_PROVIDER: {settings.APP_DATA_DATABASE_PROVIDER}. "
        "Use 'sql' or 'mock'."
    )
