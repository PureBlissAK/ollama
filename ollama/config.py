"""Configuration module for Ollama."""

from functools import lru_cache
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # Server
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    workers: int = Field(default=4, description="Number of workers")
    log_level: str = Field(default="INFO", description="Logging level")
    public_url: str = Field(default="http://localhost:8000", description="Public URL")

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://ollama:changeme@postgres:5432/ollama",
        description="PostgreSQL connection URL",
    )
    database_pool_size: int = Field(default=20, description="DB pool size")

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis connection URL")
    redis_password: Optional[str] = Field(default=None, description="Redis password")

    # Qdrant
    qdrant_host: str = Field(default="localhost", description="Qdrant host")
    qdrant_port: int = Field(default=6333, description="Qdrant port")

    # Ollama
    ollama_base_url: str = Field(
        default="http://localhost:11434", description="Ollama inference engine URL"
    )

    # Authentication
    jwt_secret: str = Field(
        description="JWT signing secret key. REQUIRED in production. See .env.example"
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(default=60, description="Access token expiration")
    refresh_token_expire_days: int = Field(default=7, description="Refresh token expiration")

    # Rate Limiting
    rate_limit_per_minute: int = Field(default=60, description="Global rate limit per minute")
    rate_limit_burst: int = Field(default=100, description="Rate limit burst size")
    ollama_request_timeout: float = Field(default=300.0, description="Request timeout")
    ollama_connect_timeout: float = Field(default=10.0, description="Connection timeout")

    # CORS
    cors_origins: List[str] = Field(default=["*"], description="Allowed CORS origins")
    cors_allow_credentials: bool = Field(default=True)
    cors_expose_headers: List[str] = Field(default=["Content-Type"])

    # Security
    trusted_hosts: Optional[List[str]] = Field(default=None, description="Trusted host names")
    api_key_auth_enabled: bool = Field(default=False)

    # Models
    models_path: str = Field(default="/models", description="Path to model files")

    # GPU
    cuda_visible_devices: str = Field(default="0", description="CUDA device IDs")


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
