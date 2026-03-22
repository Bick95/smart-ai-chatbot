"""Run SQL migrations once at application startup (optional)."""

from __future__ import annotations

import logging

import asyncpg

from src.auth.adapters.postgres.migrations import run_migrations
from src.settings import settings

logger = logging.getLogger(__name__)


def _migration_database_url() -> str | None:
    if settings.MIGRATION_DATABASE_URL is not None:
        return settings.MIGRATION_DATABASE_URL.get_secret_value()
    if settings.DATABASE_URL is not None:
        return settings.DATABASE_URL.get_secret_value()
    if settings.APP_DATA_DATABASE_URL is not None:
        return settings.APP_DATA_DATABASE_URL.get_secret_value()
    if settings.SUPABASE_DATABASE_URL is not None:
        return settings.SUPABASE_DATABASE_URL.get_secret_value()
    return None


async def run_migrations_on_startup() -> None:
    """Apply pending migrations using a privileged URL when configured.

    Prefer MIGRATION_DATABASE_URL (superuser / owner) so runtime can use chatbot_app.
    Falls back to DATABASE_URL only when MIGRATION_DATABASE_URL is unset (dev / legacy).
    """
    if not settings.RUN_MIGRATIONS_ON_STARTUP:
        logger.info("Skipping DB migrations (RUN_MIGRATIONS_ON_STARTUP=false)")
        return

    if settings.AUTH_PROVIDER.lower() == "mock" and settings.APP_DATA_PROVIDER.lower() == "mock":
        logger.info("Skipping DB migrations (mock auth and mock app data)")
        return

    url = _migration_database_url()
    if not url:
        logger.warning("No database URL for migrations; skipping")
        return

    logger.info("Running database migrations (startup)")
    pool = await asyncpg.create_pool(
        url,
        min_size=1,
        max_size=2,
        command_timeout=120,
    )
    try:
        await run_migrations(pool)
        logger.info("Database migrations complete")
    finally:
        await pool.close()
