"""Unit tests for Postgres migration helpers (mocked DB; no real cluster)."""

from __future__ import annotations

import logging
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import SecretStr

from src.auth.adapters.postgres import migrations as mig


class _AcquireCtx:
    def __init__(self, conn: AsyncMock) -> None:
        self._conn = conn

    async def __aenter__(self) -> AsyncMock:
        return self._conn

    async def __aexit__(self, *args: object) -> bool:
        return False


def _pool_with_conn(conn: AsyncMock) -> MagicMock:
    pool = MagicMock()
    pool.acquire = MagicMock(return_value=_AcquireCtx(conn))
    return pool


def _settings(
    *,
    app_provider: str = "mock",
    auth_provider: str = "mock",
    app_user: str | None = None,
    app_password: SecretStr | None = None,
    auth_user: str | None = None,
    auth_password: SecretStr | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        APP_DATA_DATABASE_PROVIDER=app_provider,
        APP_DATA_DATABASE_USERNAME=app_user,
        APP_DATA_DATABASE_PASSWORD=app_password,
        AUTHENTICATION_SERVICE_PROVIDER=auth_provider,
        AUTHENTICATION_SERVICE_USERNAME=auth_user,
        AUTHENTICATION_SERVICE_PASSWORD=auth_password,
    )


@pytest.mark.unit
class TestAlterRolePassword:
    @pytest.mark.asyncio
    async def test_uses_format_query_then_executes_returned_ddl(self) -> None:
        conn = AsyncMock()
        conn.fetchval = AsyncMock(
            return_value="ALTER ROLE \"myrole\" WITH PASSWORD 'p''ass'"
        )
        conn.execute = AsyncMock()

        await mig._alter_role_password(conn, "myrole", "p'ass")

        conn.fetchval.assert_awaited_once()
        call = conn.fetchval.await_args
        assert "format('ALTER ROLE %I WITH PASSWORD %L'" in call[0][0]
        assert call[0][1:] == ("myrole", "p'ass")

        conn.execute.assert_awaited_once_with(
            "ALTER ROLE \"myrole\" WITH PASSWORD 'p''ass'"
        )


@pytest.mark.unit
class TestApplyRuntimeRolePasswordsFromSettings:
    @pytest.mark.asyncio
    async def test_no_pool_use_when_nothing_configured(self) -> None:
        pool = _pool_with_conn(AsyncMock())
        mock_settings = _settings()

        with patch("src.settings.settings", mock_settings):
            await mig.apply_runtime_role_passwords_from_settings(pool)

        pool.acquire.assert_not_called()

    @pytest.mark.asyncio
    async def test_app_data_sql_role_applies_password(self) -> None:
        conn = AsyncMock()
        conn.fetchval = AsyncMock(return_value="ALTER ROLE a WITH PASSWORD 'x'")
        conn.execute = AsyncMock()
        pool = _pool_with_conn(conn)
        mock_settings = _settings(
            app_provider="sql",
            app_user="appuser",
            app_password=SecretStr("secret-app"),
        )

        with patch("src.settings.settings", mock_settings):
            await mig.apply_runtime_role_passwords_from_settings(pool)

        conn.fetchval.assert_awaited()
        conn.execute.assert_awaited_once_with("ALTER ROLE a WITH PASSWORD 'x'")
        fetch_kw = conn.fetchval.await_args
        assert fetch_kw[0][1:] == ("appuser", "secret-app")

    @pytest.mark.asyncio
    async def test_skips_app_data_when_password_missing(self) -> None:
        conn = AsyncMock()
        pool = _pool_with_conn(conn)
        mock_settings = _settings(
            app_provider="sql",
            app_user="appuser",
            app_password=None,
        )

        with patch("src.settings.settings", mock_settings):
            await mig.apply_runtime_role_passwords_from_settings(pool)

        pool.acquire.assert_not_called()

    @pytest.mark.asyncio
    async def test_same_role_auth_password_wins_and_logs_warning(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        conn = AsyncMock()
        conn.fetchval = AsyncMock(return_value="ddl")
        conn.execute = AsyncMock()
        pool = _pool_with_conn(conn)
        mock_settings = _settings(
            app_provider="sql",
            app_user="shared",
            app_password=SecretStr("from-app"),
            auth_provider="sql",
            auth_user="shared",
            auth_password=SecretStr("from-auth"),
        )

        with caplog.at_level(logging.WARNING):
            with patch("src.settings.settings", mock_settings):
                await mig.apply_runtime_role_passwords_from_settings(pool)

        assert any(
            "Different passwords in env for role shared" in r.message
            for r in caplog.records
        )
        conn.fetchval.assert_awaited_once()
        assert conn.fetchval.await_args[0][1:] == ("shared", "from-auth")

    @pytest.mark.asyncio
    async def test_two_roles_sorted_alphabetically(self) -> None:
        conn = AsyncMock()
        conn.fetchval = AsyncMock(side_effect=["ddl_z", "ddl_a"])
        conn.execute = AsyncMock()
        pool = _pool_with_conn(conn)
        mock_settings = _settings(
            app_provider="sql",
            app_user="zebra",
            app_password=SecretStr("pz"),
            auth_provider="sql",
            auth_user="alpha",
            auth_password=SecretStr("pa"),
        )

        with patch("src.settings.settings", mock_settings):
            await mig.apply_runtime_role_passwords_from_settings(pool)

        assert conn.fetchval.await_args_list[0][0][1:] == ("alpha", "pa")
        assert conn.fetchval.await_args_list[1][0][1:] == ("zebra", "pz")


@pytest.mark.unit
class TestRunMigrations:
    @pytest.mark.asyncio
    async def test_empty_migration_dir_still_calls_apply_passwords(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        conn = AsyncMock()
        pool = _pool_with_conn(conn)
        mock_settings = _settings()

        with patch.object(mig, "MIGRATIONS_DIR", tmp_path):
            with patch("src.settings.settings", mock_settings):
                with caplog.at_level(logging.WARNING):
                    await mig.run_migrations(pool)

        assert any("No migration files found" in r.message for r in caplog.records)
        pool.acquire.assert_not_called()

    @pytest.mark.asyncio
    async def test_applies_pending_files_then_password_sync(
        self, tmp_path: Path
    ) -> None:
        (tmp_path / "001_a.sql").write_text("CREATE TABLE a();")
        (tmp_path / "002_b.sql").write_text("CREATE TABLE b();")

        conn = AsyncMock()
        conn.fetchrow = AsyncMock(return_value=None)
        conn.execute = AsyncMock()
        conn.fetchval = AsyncMock(return_value="ALTER ROLE u WITH PASSWORD 'p'")
        pool = _pool_with_conn(conn)

        mock_settings = _settings(
            app_provider="sql",
            app_user="u",
            app_password=SecretStr("p"),
        )

        with patch.object(mig, "MIGRATIONS_DIR", tmp_path):
            with patch("src.settings.settings", mock_settings):
                await mig.run_migrations(pool)

        exec_calls = [c.args[0] for c in conn.execute.await_args_list]
        assert any(
            "CREATE TABLE IF NOT EXISTS _migrations" in str(c) for c in exec_calls
        )
        assert "CREATE TABLE a();" in exec_calls
        assert "CREATE TABLE b();" in exec_calls
        inserts = [
            c for c in conn.execute.await_args_list if c.args[0].startswith("INSERT")
        ]
        assert len(inserts) == 2
        assert conn.fetchval.await_args[0][1:] == ("u", "p")

    @pytest.mark.asyncio
    async def test_skips_already_applied_migration(self, tmp_path: Path) -> None:
        (tmp_path / "001_only.sql").write_text("SELECT 1;")

        conn = AsyncMock()

        async def fetchrow(*_a: object, **_k: object) -> MagicMock | None:
            return MagicMock()  # row exists -> skip

        conn.fetchrow = AsyncMock(side_effect=fetchrow)
        conn.execute = AsyncMock()
        pool = _pool_with_conn(conn)
        mock_settings = _settings()

        with patch.object(mig, "MIGRATIONS_DIR", tmp_path):
            with patch("src.settings.settings", mock_settings):
                await mig.run_migrations(pool)

        exec_calls = [c.args[0] for c in conn.execute.await_args_list]
        assert "SELECT 1;" not in exec_calls
        assert not any(
            c.args[0].startswith("INSERT") for c in conn.execute.await_args_list
        )
