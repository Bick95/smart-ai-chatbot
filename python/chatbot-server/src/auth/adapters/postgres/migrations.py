"""Run Postgres migrations on startup."""

from __future__ import annotations

import asyncpg
from pathlib import Path

from src.utils.logging import get_logger

_logger = get_logger(__name__)
MIGRATIONS_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent.parent / "migrations"
)


async def _alter_role_password(
    conn: asyncpg.Connection, role_name: str, password: str
) -> None:
    """Set role password. Postgres rejects prepared ALTER ROLE ... PASSWORD $1; use format()."""
    ddl = await conn.fetchval(
        "SELECT format('ALTER ROLE %I WITH PASSWORD %L', $1::text, $2::text)",
        role_name,
        password,
    )
    await conn.execute(ddl)


async def apply_runtime_role_passwords_from_settings(pool: asyncpg.Pool) -> None:
    """Sync SQL role passwords from environment (no passwords in migration SQL)."""
    from src.settings import settings

    role_password: dict[str, str] = {}

    if (
        settings.APP_DATA_DATABASE_PROVIDER.lower() == "sql"
        and settings.APP_DATA_DATABASE_USERNAME
        and settings.APP_DATA_DATABASE_PASSWORD is not None
    ):
        role_password[settings.APP_DATA_DATABASE_USERNAME] = (
            settings.APP_DATA_DATABASE_PASSWORD.get_secret_value()
        )

    if (
        settings.AUTHENTICATION_SERVICE_PROVIDER.lower() == "sql"
        and settings.AUTHENTICATION_SERVICE_USERNAME
        and settings.AUTHENTICATION_SERVICE_PASSWORD is not None
    ):
        u = settings.AUTHENTICATION_SERVICE_USERNAME
        p = settings.AUTHENTICATION_SERVICE_PASSWORD.get_secret_value()
        if u in role_password and role_password[u] != p:
            _logger.warning(
                "Different passwords in env for role %s (APP_DATA_DATABASE_PASSWORD vs "
                "AUTHENTICATION_SERVICE_PASSWORD); using AUTHENTICATION_SERVICE_PASSWORD",
                u,
            )
        role_password[u] = p

    if not role_password:
        return

    async with pool.acquire() as conn:
        for role_name, password in sorted(role_password.items()):
            await _alter_role_password(conn, role_name, password)
            _logger.info("Applied password from env for role %s", role_name)


async def run_migrations(pool: asyncpg.Pool) -> None:
    """Run pending SQL migrations in order."""
    sql_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    if not sql_files:
        _logger.warning("No migration files found in %s", MIGRATIONS_DIR)
        return

    _logger.info("Running migrations")
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS _migrations (
                name TEXT PRIMARY KEY,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """)

        for path in sql_files:
            name = path.name
            row = await conn.fetchrow("SELECT 1 FROM _migrations WHERE name = $1", name)
            if row is not None:
                continue

            sql = path.read_text()
            await conn.execute(sql)
            await conn.execute("INSERT INTO _migrations (name) VALUES ($1)", name)
            _logger.info("Applied migration: %s", name)

    _logger.info("Migrations complete")
    await apply_runtime_role_passwords_from_settings(pool)
