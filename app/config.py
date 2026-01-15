"""Application configuration."""

from functools import lru_cache
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Application
    app_name: str = Field(default="CoreRecon SOC", alias="APP_NAME")
    app_version: str = Field(default="1.0.0", alias="APP_VERSION")
    env: str = Field(default="development", alias="ENV")
    debug: bool = Field(default=False, alias="DEBUG")

    # Server
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")
    workers: int = Field(default=4, alias="WORKERS")

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://soc_user:changeme@localhost:5432/soc_db",
        alias="DATABASE_URL"
    )
    database_pool_size: int = Field(default=20, alias="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=10, alias="DATABASE_MAX_OVERFLOW")

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    redis_password: Optional[str] = Field(default=None, alias="REDIS_PASSWORD")

    # Elasticsearch
    elasticsearch_url: str = Field(
        default="http://localhost:9200",
        alias="ELASTICSEARCH_URL"
    )
    elasticsearch_username: str = Field(default="elastic", alias="ELASTICSEARCH_USERNAME")
    elasticsearch_password: str = Field(default="changeme", alias="ELASTICSEARCH_PASSWORD")
    elasticsearch_index_prefix: str = Field(
        default="corerecon-soc",
        alias="ELASTICSEARCH_INDEX_PREFIX"
    )

    # Security
    secret_key: str = Field(
        default="changeme-generate-a-secure-secret-key-here",
        alias="SECRET_KEY"
    )
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=30,
        alias="ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    refresh_token_expire_days: int = Field(
        default=7,
        alias="REFRESH_TOKEN_EXPIRE_DAYS"
    )

    # CORS
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        alias="CORS_ORIGINS"
    )
    cors_allow_credentials: bool = Field(default=True, alias="CORS_ALLOW_CREDENTIALS")

    # Elastic SIEM
    elastic_siem_url: Optional[str] = Field(default=None, alias="ELASTIC_SIEM_URL")
    elastic_siem_api_key: Optional[str] = Field(default=None, alias="ELASTIC_SIEM_API_KEY")
    elastic_siem_webhook_secret: Optional[str] = Field(
        default=None,
        alias="ELASTIC_SIEM_WEBHOOK_SECRET"
    )

    # Cloud Platforms
    azure_tenant_id: Optional[str] = Field(default=None, alias="AZURE_TENANT_ID")
    azure_client_id: Optional[str] = Field(default=None, alias="AZURE_CLIENT_ID")
    azure_client_secret: Optional[str] = Field(default=None, alias="AZURE_CLIENT_SECRET")

    aws_region: str = Field(default="us-east-1", alias="AWS_REGION")
    aws_access_key_id: Optional[str] = Field(default=None, alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = Field(default=None, alias="AWS_SECRET_ACCESS_KEY")

    gcp_project_id: Optional[str] = Field(default=None, alias="GCP_PROJECT_ID")
    gcp_credentials_path: Optional[str] = Field(default=None, alias="GCP_CREDENTIALS_PATH")

    # Performance
    cache_ttl: int = Field(default=300, alias="CACHE_TTL")
    max_websocket_connections: int = Field(
        default=5000,
        alias="MAX_WEBSOCKET_CONNECTIONS"
    )

    # SLA Configuration (minutes)
    sla_critical_first_response: int = Field(
        default=15,
        alias="SLA_CRITICAL_FIRST_RESPONSE"
    )
    sla_critical_resolution: int = Field(
        default=240,
        alias="SLA_CRITICAL_RESOLUTION"
    )
    sla_high_first_response: int = Field(default=60, alias="SLA_HIGH_FIRST_RESPONSE")
    sla_high_resolution: int = Field(default=480, alias="SLA_HIGH_RESOLUTION")

    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_format: str = Field(default="json", alias="LOG_FORMAT")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
