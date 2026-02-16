from __future__ import annotations

from pydantic import SecretStr, Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local"),
        _env_file_encoding="utf-8",
        env_prefix="",
        env_nested_delimiter=",",
        extra="ignore"
    )

    DEBUG: bool = Field(default=False)

    # Server (for programmatic runs)
    HOST: str = Field(default="0.0.0.0", description="Server bind host")
    PORT: int = Field(default=8000, ge=1, le=65535, description="Server port")

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
