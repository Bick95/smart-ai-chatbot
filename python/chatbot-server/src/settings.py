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

    # Secrets
    OPENAI_API_KEY: SecretStr

settings = Settings()
