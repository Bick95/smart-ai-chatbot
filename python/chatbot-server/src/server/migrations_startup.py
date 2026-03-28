"""Run SQL migrations once at application startup (optional)."""

from __future__ import annotations

import logging

import asyncpg

from src.auth.adapters.postgres.migrations import run_migrations
from src.settings import settings

logger = logging.getLogger(__name__)


def _migration_database_url() -> str | None:
    """Privileged URL for migrations (APP_DATA_DATABASE_ADMIN_*)."""
    return settings.app_data_database_admin_url()


async def run_migrations_on_startup() -> None:
    """Apply pending migrations using APP_DATA_DATABASE_ADMIN_* when configured.

    Skips when both auth and app data are mock, or when migrations are disabled.
    """
    if not settings.APP_DATA_DATABASE_RUN_MIGRATIONS_ON_STARTUP:
        logger.info(
            "Skipping DB migrations (APP_DATA_DATABASE_RUN_MIGRATIONS_ON_STARTUP=false)"
        )
        return

    if (
        settings.AUTHENTICATION_SERVICE_PROVIDER.lower() == "mock"
        and settings.APP_DATA_DATABASE_PROVIDER.lower() == "mock"
    ):
        logger.info("Skipping DB migrations (mock auth and mock app data)")
        return

    url = _migration_database_url()
    if not url:
        logger.warning(
            "No APP_DATA_DATABASE_ADMIN_* credentials for migrations; skipping "
            "(set APP_DATA_DATABASE_ADMIN_USERNAME and APP_DATA_DATABASE_ADMIN_PASSWORD)"
        )
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
