"""Tests for database URL building and equality (no network)."""

from __future__ import annotations

import pytest

from src.utils.database_connection_url import (
    build_database_connection_url,
    database_connection_urls_equivalent,
)


@pytest.mark.unit
class TestBuildDatabaseConnectionUrl:
    def test_round_trip_components(self) -> None:
        url = build_database_connection_url(
            host="db.example.com",
            port=5432,
            database="app",
            username="appuser",
            password="s3cret",
        )
        assert url == "postgresql://appuser:s3cret@db.example.com:5432/app"

    def test_quotes_special_characters_in_user_and_password(self) -> None:
        url = build_database_connection_url(
            host="localhost",
            port=5432,
            database="d",
            username="user@tenant",
            password="p:w&d%",
        )
        assert url == "postgresql://user%40tenant:p%3Aw%26d%25@localhost:5432/d"

    def test_non_default_port(self) -> None:
        url = build_database_connection_url(
            host="127.0.0.1",
            port=15432,
            database="mydb",
            username="u",
            password="p",
        )
        assert url == "postgresql://u:p@127.0.0.1:15432/mydb"


@pytest.mark.unit
class TestDatabaseConnectionUrlsEquivalent:
    def test_same_string(self) -> None:
        u = "postgresql://a:b@h:5432/db"
        assert database_connection_urls_equivalent(u, u) is True

    def test_postgres_and_postgresql_schemes_equivalent(self) -> None:
        a = "postgresql://user:pass@host:5432/mydb"
        b = "postgres://user:pass@host:5432/mydb"
        assert database_connection_urls_equivalent(a, b) is True

    def test_percent_encoding_same_credentials(self) -> None:
        built = build_database_connection_url(
            host="h",
            port=5432,
            database="db",
            username="u@x",
            password="a:b",
        )
        assert database_connection_urls_equivalent(
            built,
            "postgresql://u%40x:a%3Ab@h:5432/db",
        )

    def test_default_port_omitted_vs_explicit_5432(self) -> None:
        a = "postgresql://u:p@host:5432/db"
        b = "postgresql://u:p@host/db"
        assert database_connection_urls_equivalent(a, b) is True

    def test_false_when_password_differs(self) -> None:
        a = "postgresql://u:one@host:5432/db"
        b = "postgresql://u:two@host:5432/db"
        assert database_connection_urls_equivalent(a, b) is False

    def test_false_when_host_differs(self) -> None:
        a = "postgresql://u:p@a:5432/db"
        b = "postgresql://u:p@b:5432/db"
        assert database_connection_urls_equivalent(a, b) is False

    def test_false_when_database_differs(self) -> None:
        a = "postgresql://u:p@h:5432/db1"
        b = "postgresql://u:p@h:5432/db2"
        assert database_connection_urls_equivalent(a, b) is False

    def test_invalid_scheme_raises(self) -> None:
        with pytest.raises(ValueError, match="Expected scheme postgresql"):
            database_connection_urls_equivalent(
                "mysql://u:p@h:5432/db",
                "postgresql://u:p@h:5432/db",
            )
