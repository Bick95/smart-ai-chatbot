"""Run Postgres migrations on startup."""

from __future__ import annotations

import asyncpg
from pathlib import Path

from src.utils.logging import get_logger

_logger = get_logger(__name__)
MIGRATIONS_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / "migrations"


async def run_migrations(pool: asyncpg.Pool) -> None:
    """Run pending SQL migrations in order."""
    sql_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    if not sql_files:
        _logger.warning("No migration files found in %s", MIGRATIONS_DIR)
        return

    async with pool.acquire() as conn:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS _migrations (
                name TEXT PRIMARY KEY,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )

        for path in sql_files:
            name = path.name
            row = await conn.fetchrow(
                "SELECT 1 FROM _migrations WHERE name = $1", name
            )
            if row is not None:
                continue

            sql = path.read_text()
            await conn.execute(sql)
            await conn.execute(
                "INSERT INTO _migrations (name) VALUES ($1)", name
            )
