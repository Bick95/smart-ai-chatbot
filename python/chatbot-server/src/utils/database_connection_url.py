"""Build and compare SQL database connection URLs from explicit components (driver-agnostic naming)."""

from __future__ import annotations

from urllib.parse import quote_plus, unquote, urlparse


def build_database_connection_url(
    *,
    host: str,
    port: int,
    database: str,
    username: str,
    password: str,
) -> str:
    """Build a SQL connection URL from discrete settings (used by the SQL adapters)."""
    return (
        f"postgresql://{quote_plus(username)}:{quote_plus(password)}"
        f"@{host}:{port}/{database}"
    )


def _connection_url_parts(url: str) -> tuple[str, str, str, str, str]:
    """Return (host, port, database, username, password) for equality checks."""
    p = urlparse(url)
    if p.scheme not in ("postgresql", "postgres"):
        raise ValueError(f"Expected scheme postgresql or postgres, got {p.scheme!r}")
    host = p.hostname or ""
    port = str(p.port or 5432)
    database = (p.path or "/").lstrip("/").split("/")[0] or ""
    user = unquote(p.username or "")
    pw = unquote(p.password or "")
    return (host, port, database, user, pw)


def database_connection_urls_equivalent(a: str, b: str) -> bool:
    """True if two URLs refer to the same host, database, and credentials."""
    return _connection_url_parts(a) == _connection_url_parts(b)
