from pydantic import SecretStr, Field
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

settings = Settings()
