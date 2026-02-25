from __future__ import annotations

from pydantic import Field, SecretStr, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local"),
        _env_file_encoding="utf-8",
        env_prefix="",
        env_nested_delimiter=",",
        extra="ignore",
    )

    DEBUG: bool = Field(default=False)

    # Server (for programmatic runs)
    HOST: str = Field(default="0.0.0.0", description="Server bind host")
    PORT: int = Field(default=8000, ge=1, le=65535, description="Server port")

    # API docs (Swagger/ReDoc); disable in production for security
    ENABLE_DOCS: bool = Field(
        default=True,
        description="Expose /docs and /redoc endpoints",
    )

    # Input limits for chat API
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

    # CORS (comma-separated origins, or * for all; * is insecure in production)
    CORS_ORIGINS: str = Field(
        default="*",
        description="Comma-separated allowed origins (e.g. https://app.example.com) or * for all",
    )

    # Optional: prompt API for live refresh (no redeploy needed)
    PROMPT_API_URL: str | None = Field(
        default=None,
        description="URL to fetch prompts from; if set, prompts are refreshed periodically",
    )
    PROMPT_REFRESH_INTERVAL_SECONDS: float = Field(
        default=300,
        ge=60,
        description="Seconds between prompt API refreshes (min 60)",
    )

    # Auth (hexagonal: postgres or supabase adapter)
    AUTH_ENABLED: bool = Field(
        default=False,
        description="Enable auth; when True, AUTH_PROVIDER and its config are required",
    )
    AUTH_PROVIDER: str = Field(
        default="postgres",
        description="Auth adapter: 'postgres' or 'supabase' (used when AUTH_ENABLED=True)",
    )
    DATABASE_URL: SecretStr | None = Field(
        default=None,
        description="Postgres connection URL (required when AUTH_PROVIDER=postgres)",
    )
    SUPABASE_URL: str = Field(
        default="",
        description="Supabase project URL (required when AUTH_PROVIDER=supabase)",
    )
    SUPABASE_SERVICE_ROLE_KEY: SecretStr | None = Field(
        default=None,
        description="Supabase service_role key (required when AUTH_PROVIDER=supabase)",
    )
    SUPABASE_DATABASE_URL: SecretStr | None = Field(
        default=None,
        description="Supabase Postgres connection URL; when set, get_user_by_email uses "
        "efficient direct query on auth.users instead of list_users",
    )
    JWT_SECRET_KEY: SecretStr | None = Field(
        default=None,
        description="Secret for signing JWTs (required when AUTH_ENABLED=True)",
    )
    JWT_AUTH_TTL_SECONDS: int = Field(
        default=900,
        ge=60,
        description="Auth JWT TTL in seconds (default 15 min)",
    )
    JWT_REFRESH_TTL_SECONDS: int = Field(
        default=86400,
        ge=3600,
        description="Refresh JWT TTL in seconds (default 24 h)",
    )

    # Secrets
    OPENAI_API_KEY: SecretStr

    @computed_field
    @property
    def cors_origins_list(self) -> list[str]:
        """Parsed CORS origins for CORSMiddleware."""
        if self.CORS_ORIGINS.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()
