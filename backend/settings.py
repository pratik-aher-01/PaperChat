"""Application settings loaded from environment variables."""

from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from config import (
    DEFAULT_APP_NAME,
    DEFAULT_APP_VERSION,
    DEFAULT_CORS_ORIGINS,
    DEFAULT_HOST,
    DEFAULT_LOG_LEVEL,
    DEFAULT_PORT,
)


class Settings(BaseSettings):
    """Runtime configuration for PaperChat."""

    app_name: str = Field(default=DEFAULT_APP_NAME, alias="APP_NAME")
    app_version: str = Field(default=DEFAULT_APP_VERSION, alias="APP_VERSION")
    debug: bool = Field(default=False, alias="DEBUG")
    host: str = Field(default=DEFAULT_HOST, alias="HOST")
    port: int = Field(default=DEFAULT_PORT, alias="PORT")
    log_level: str = Field(default=DEFAULT_LOG_LEVEL, alias="LOG_LEVEL")
    cors_origins: str | tuple[str, ...] = Field(
        default=DEFAULT_CORS_ORIGINS,
        alias="CORS_ORIGINS",
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Any) -> tuple[str, ...]:
        """Parse comma-separated CORS origins from strings."""
        if isinstance(value, str):
            return tuple(origin.strip() for origin in value.split(",") if origin.strip())
        return value

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug(cls, value: Any) -> Any:
        """Normalize common environment labels into a debug boolean."""
        if isinstance(value, str) and value.lower() in {"release", "production", "prod"}:
            return False
        if isinstance(value, str) and value.lower() in {"development", "dev"}:
            return True
        return value

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Any) -> Any:
        """Parse comma-separated CORS origins."""
        if isinstance(value, str):
            return tuple(origin.strip() for origin in value.split(",") if origin.strip())
        return value

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
