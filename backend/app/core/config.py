"""Application settings, loaded from environment variables and an optional .env file."""

from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # App
    app_name: str = "Scholarship Finder API"
    environment: str = "development"
    log_level: str = "INFO"
    cors_origins: list[str] = ["http://localhost:5173"]

    # fastn MCP gateway
    fastn_mcp_url: str = "https://mcp.fastn.dev"
    fastn_api_key: SecretStr | None = None
    fastn_auth_header: str = "Authorization"
    fastn_auth_scheme: str = "Bearer"  # set to "" to send the raw key
    fastn_extra_headers: dict[str, str] = {}
    fastn_timeout_seconds: float = Field(default=30.0, gt=0)
    fastn_max_retries: int = Field(default=2, ge=0)


@lru_cache
def get_settings() -> Settings:
    return Settings()
