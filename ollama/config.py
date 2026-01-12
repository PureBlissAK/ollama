"""Configuration module for Ollama."""

from functools import lru_cache
from typing import List, Optional
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
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
        description="PostgreSQL connection URL"
    )
    database_pool_size: int = Field(default=20, description="DB pool size")
    
    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )
    redis_password: Optional[str] = Field(default=None, description="Redis password")
    
    # Qdrant
    qdrant_host: str = Field(default="localhost", description="Qdrant host")
    qdrant_port: int = Field(default=6333, description="Qdrant port")
    
    # CORS
    cors_origins: List[str] = Field(
        default=["*"],
        description="Allowed CORS origins"
    )
    cors_allow_credentials: bool = Field(default=True)
    cors_expose_headers: List[str] = Field(default=["Content-Type"])
    
    # Security
    trusted_hosts: Optional[List[str]] = Field(
        default=None,
        description="Trusted host names"
    )
    api_key_auth_enabled: bool = Field(default=False)
    
    # Models
    models_path: str = Field(default="/models", description="Path to model files")
    
    # GPU
    cuda_visible_devices: str = Field(default="0", description="CUDA device IDs")


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()

    @classmethod
    def from_env(cls) -> "OllamaConfig":
        """Load configuration from environment variables."""
        config_path = os.getenv("OLLAMA_CONFIG", "config/development.yaml")
        return cls.from_file(config_path)
