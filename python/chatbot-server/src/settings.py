from __future__ import annotations

from pydantic import Field, SecretStr, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.utils.database_connection_url import build_database_connection_url


def _auth_uses_sql_adapter(provider: str) -> bool:
    return provider.lower() == "sql"


def _app_uses_sql_adapter(provider: str) -> bool:
    return provider.lower() == "sql"


class Settings(BaseSettings):
    """Application configuration loaded from environment / .env files.

    **Authentication service** (``AUTHENTICATION_SERVICE_*``) — controlled by
    ``AUTHENTICATION_SERVICE_PROVIDER``:

    - **sql:** ``AUTHENTICATION_SERVICE_USERNAME``, ``AUTHENTICATION_SERVICE_PASSWORD``,
      using the **application data database cluster** (``APP_DATA_DATABASE_HOST`` etc.) for the DSN.
    - **supabase:** ``AUTHENTICATION_SERVICE_URL``, ``AUTHENTICATION_SERVICE_PASSWORD``
      (service role). Optionally ``AUTHENTICATION_SERVICE_DATABASE_URL`` for direct SQL.

    **Application data database** (``APP_DATA_DATABASE_*``) — provider, host, port, database name,
    runtime user, privileged admin user for migrations.

    If authentication and application data use the same connection parameters,
    ``authentication_service_database_url()`` and ``app_data_database_url()`` match and the API
    reuses a single pool.
    """

    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local"),
        env_file_encoding="utf-8",
        env_prefix="",
        env_nested_delimiter=",",
        extra="ignore",
    )

    DEBUG: bool = Field(default=False)

    HOST: str = Field(default="0.0.0.0", description="Server bind host")
    PORT: int = Field(default=8000, ge=1, le=65535, description="Server port")

    ENABLE_DOCS: bool = Field(
        default=True,
        description="Expose /docs and /redoc endpoints",
    )

    MAX_CHAT_MESSAGES: int = Field(
        default=50,
        ge=1,
        le=500,
        description="Maximum number of messages per chat request",
    )
    MAX_MESSAGE_CONTENT_LENGTH: int = Field(
        default=16_384,
        ge=1,
        le=1_000_000,
        description="Maximum character length per message content",
    )

    CORS_ORIGINS: str = Field(
        default="*",
        description="Comma-separated allowed origins or * for all",
    )

    PROMPT_API_URL: str | None = Field(
        default=None,
        description="Optional HTTP base for prompt refresh",
    )
    PROMPT_REFRESH_INTERVAL_SECONDS: float = Field(
        default=300,
        ge=60,
        description="Seconds between prompt API refreshes",
    )

    # --- Authentication service (AUTHENTICATION_SERVICE_PROVIDER: sql | supabase | mock) ---
    AUTHENTICATION_SERVICE_PROVIDER: str = Field(
        default="sql",
        description="'sql', 'supabase', or 'mock'",
    )
    AUTHENTICATION_SERVICE_URL: str = Field(
        default="",
        description="Project base URL when AUTHENTICATION_SERVICE_PROVIDER=supabase (e.g. https://….supabase.co)",
    )
    AUTHENTICATION_SERVICE_USERNAME: str | None = Field(
        default=None,
        description="Database user when AUTHENTICATION_SERVICE_PROVIDER=sql",
    )
    AUTHENTICATION_SERVICE_PASSWORD: SecretStr | None = Field(
        default=None,
        description="Database password when AUTHENTICATION_SERVICE_PROVIDER=sql; service role secret when AUTHENTICATION_SERVICE_PROVIDER=supabase",
    )
    AUTHENTICATION_SERVICE_DATABASE_URL: SecretStr | None = Field(
        default=None,
        description="Optional direct database URL for the auth adapter (e.g. Supabase auth.users)",
    )

    # --- Application data database (APP_DATA_DATABASE_*) ---
    APP_DATA_DATABASE_PROVIDER: str = Field(
        default="sql",
        description="'sql' or 'mock'",
    )
    APP_DATA_DATABASE_HOST: str = Field(
        default="localhost",
        description="Hostname for application data (SQL)",
    )
    APP_DATA_DATABASE_PORT: int = Field(default=5432, ge=1, le=65535)
    APP_DATA_DATABASE_NAME: str = Field(
        default="chatbot",
        description="Database name for application data",
    )
    APP_DATA_DATABASE_USERNAME: str | None = Field(
        default=None,
        description="Runtime user when APP_DATA_DATABASE_PROVIDER=sql",
    )
    APP_DATA_DATABASE_PASSWORD: SecretStr | None = Field(
        default=None,
        description="Password for APP_DATA_DATABASE_USERNAME",
    )
    APP_DATA_DATABASE_RUN_MIGRATIONS_ON_STARTUP: bool = Field(
        default=True,
        description="Apply SQL migrations at startup using APP_DATA_DATABASE_ADMIN_*",
    )
    APP_DATA_DATABASE_ADMIN_USERNAME: str | None = Field(
        default=None,
        description="Privileged user for schema migrations",
    )
    APP_DATA_DATABASE_ADMIN_PASSWORD: SecretStr | None = Field(
        default=None,
        description="Password for APP_DATA_DATABASE_ADMIN_USERNAME",
    )

    JWT_SECRET_KEY: SecretStr | None = Field(
        default=None,
        description="Secret for signing JWTs (required outside tests)",
    )
    JWT_AUTH_TTL_SECONDS: int = Field(default=900, ge=60)
    JWT_REFRESH_TTL_SECONDS: int = Field(default=86400, ge=3600)
    SIGNUP_INVITE_KEY: SecretStr | None = Field(
        default=None,
        description="Optional invite key for signup",
    )

    OPENAI_API_KEY: SecretStr

    @computed_field
    def cors_origins_list(self) -> list[str]:
        if self.CORS_ORIGINS.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    def authentication_service_uses_sql(self) -> bool:
        return _auth_uses_sql_adapter(self.AUTHENTICATION_SERVICE_PROVIDER)

    def app_data_database_uses_sql(self) -> bool:
        return _app_uses_sql_adapter(self.APP_DATA_DATABASE_PROVIDER)

    def authentication_service_database_url(self) -> str | None:
        """Connection URL for the SQL authentication adapter, or None if not applicable."""
        if not _auth_uses_sql_adapter(self.AUTHENTICATION_SERVICE_PROVIDER):
            return None
        if (
            not self.AUTHENTICATION_SERVICE_USERNAME
            or self.AUTHENTICATION_SERVICE_PASSWORD is None
        ):
            return None
        return build_database_connection_url(
            host=self.APP_DATA_DATABASE_HOST,
            port=self.APP_DATA_DATABASE_PORT,
            database=self.APP_DATA_DATABASE_NAME,
            username=self.AUTHENTICATION_SERVICE_USERNAME,
            password=self.AUTHENTICATION_SERVICE_PASSWORD.get_secret_value(),
        )

    def app_data_database_url(self) -> str | None:
        """Connection URL for SQL-backed application data, or None if not applicable."""
        if not _app_uses_sql_adapter(self.APP_DATA_DATABASE_PROVIDER):
            return None
        if (
            not self.APP_DATA_DATABASE_USERNAME
            or self.APP_DATA_DATABASE_PASSWORD is None
        ):
            return None
        return build_database_connection_url(
            host=self.APP_DATA_DATABASE_HOST,
            port=self.APP_DATA_DATABASE_PORT,
            database=self.APP_DATA_DATABASE_NAME,
            username=self.APP_DATA_DATABASE_USERNAME,
            password=self.APP_DATA_DATABASE_PASSWORD.get_secret_value(),
        )

    def app_data_database_admin_url(self) -> str | None:
        """Privileged connection URL for migrations."""
        if (
            not self.APP_DATA_DATABASE_ADMIN_USERNAME
            or self.APP_DATA_DATABASE_ADMIN_PASSWORD is None
        ):
            return None
        return build_database_connection_url(
            host=self.APP_DATA_DATABASE_HOST,
            port=self.APP_DATA_DATABASE_PORT,
            database=self.APP_DATA_DATABASE_NAME,
            username=self.APP_DATA_DATABASE_ADMIN_USERNAME,
            password=self.APP_DATA_DATABASE_ADMIN_PASSWORD.get_secret_value(),
        )


settings = Settings()
