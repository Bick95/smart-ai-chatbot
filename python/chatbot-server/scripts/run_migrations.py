"""Production-oriented SQL migration runner.

Usage:
  uv run python scripts/run_migrations.py
  uv run python scripts/run_migrations.py --database-url postgresql://...

Database URL resolution order:
  1) --database-url
  2) APP_DATA_DATABASE_ADMIN_* (see Settings.app_data_database_admin_url() / .env.compose.example)
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import time
from dataclasses import dataclass

import asyncpg

from src.auth.adapters.postgres.migrations import run_migrations


LOGGER = logging.getLogger("migration-runner")
# Stable 64-bit lock key for this project.
MIGRATION_LOCK_KEY = 903_882_067_507_398_111


@dataclass(frozen=True)
class RunnerConfig:
    database_url: str
    lock_timeout_seconds: int
    poll_interval_seconds: float


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run database migrations safely.")
    parser.add_argument(
        "--database-url",
        default=None,
        help="Override database URL for migrations.",
    )
    parser.add_argument(
        "--lock-timeout-seconds",
        type=int,
        default=60,
        help="How long to wait for migration lock before failing.",
    )
    parser.add_argument(
        "--poll-interval-seconds",
        type=float,
        default=1.0,
        help="Polling interval while waiting for migration lock.",
    )
    return parser.parse_args()


def _resolve_database_url(cli_database_url: str | None) -> str:
    if cli_database_url and cli_database_url.strip():
        return cli_database_url.strip()
    from src.settings import settings

    admin = settings.app_data_database_admin_url()
    if admin:
        return admin
    raise ValueError(
        "No migration database URL. Pass --database-url or set APP_DATA_DATABASE_HOST, "
        "APP_DATA_DATABASE_PORT, APP_DATA_DATABASE_NAME, APP_DATA_DATABASE_ADMIN_USERNAME, "
        "and APP_DATA_DATABASE_ADMIN_PASSWORD."
    )


async def _acquire_lock_with_timeout(
    conn: asyncpg.Connection,
    timeout_seconds: int,
    poll_interval_seconds: float,
) -> None:
    deadline = time.monotonic() + timeout_seconds
    while True:
        acquired = await conn.fetchval(
            "SELECT pg_try_advisory_lock($1)",
            MIGRATION_LOCK_KEY,
        )
        if acquired:
            return
        if time.monotonic() >= deadline:
            raise TimeoutError(
                f"Timed out after {timeout_seconds}s waiting for migration lock."
            )
        await asyncio.sleep(poll_interval_seconds)


async def _run(config: RunnerConfig) -> None:
    LOGGER.info("Connecting to database for migrations")
    pool = await asyncpg.create_pool(
        config.database_url,
        min_size=1,
        max_size=2,
        command_timeout=120,
    )
    lock_conn: asyncpg.Connection | None = None
    try:
        lock_conn = await pool.acquire()
        LOGGER.info("Acquiring migration lock")
        await _acquire_lock_with_timeout(
            lock_conn,
            timeout_seconds=config.lock_timeout_seconds,
            poll_interval_seconds=config.poll_interval_seconds,
        )
        LOGGER.info("Migration lock acquired")

        # Run existing migration mechanism (idempotent via _migrations table).
        await run_migrations(pool)
        LOGGER.info("Migrations applied successfully")
    finally:
        if lock_conn is not None:
            try:
                await lock_conn.execute(
                    "SELECT pg_advisory_unlock($1)",
                    MIGRATION_LOCK_KEY,
                )
                LOGGER.info("Migration lock released")
            finally:
                await pool.release(lock_conn)
        await pool.close()


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
    )
    args = _parse_args()
    try:
        config = RunnerConfig(
            database_url=_resolve_database_url(args.database_url),
            lock_timeout_seconds=args.lock_timeout_seconds,
            poll_interval_seconds=args.poll_interval_seconds,
        )
        asyncio.run(_run(config))
        return 0
    except Exception as exc:
        LOGGER.exception("Migration run failed: %s", type(exc).__name__)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
