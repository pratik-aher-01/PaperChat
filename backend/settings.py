"""Application settings loaded from environment variables."""

import ipaddress
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from config import (
    DEFAULT_APP_NAME,
    DEFAULT_APP_VERSION,
    DEFAULT_CORS_ORIGINS,
    DEFAULT_DOCUMENT_LAYOUT,
    DEFAULT_HOST,
    DEFAULT_LOG_LEVEL,
    DEFAULT_PDF_ENGINE,
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
    cors_origins: str | tuple[str, ...] = Field(default=DEFAULT_CORS_ORIGINS, alias="CORS_ORIGINS")
    trusted_proxy_ips: str | tuple[str, ...] = Field(default=(), alias="TRUSTED_PROXY_IPS")
    document_layout: str = Field(default=DEFAULT_DOCUMENT_LAYOUT, alias="DOCUMENT_LAYOUT")
    pdf_engine: str = Field(default=DEFAULT_PDF_ENGINE, alias="PDF_ENGINE")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Any) -> tuple[str, ...]:
        if isinstance(value, str):
            return tuple(origin.strip() for origin in value.split(",") if origin.strip())
        return tuple(value)

    @field_validator("trusted_proxy_ips", mode="before")
    @classmethod
    def parse_trusted_proxy_ips(cls, value: Any) -> tuple[ipaddress.IPv4Network | ipaddress.IPv6Network, ...]:
        if not value:
            return ()
        values = value.split(",") if isinstance(value, str) else value
        networks = []
        for item in values:
            item = str(item).strip()
            if item:
                networks.append(ipaddress.ip_network(item, strict=False))
        return tuple(networks)

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug(cls, value: Any) -> Any:
        if isinstance(value, str) and value.lower() in {"release", "production", "prod"}:
            return False
        if isinstance(value, str) and value.lower() in {"development", "dev"}:
            return True
        return value

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
