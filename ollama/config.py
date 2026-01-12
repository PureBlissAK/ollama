"""Configuration module for Ollama."""

from typing import Optional
from pathlib import Path
import yaml
import os
from dataclasses import dataclass


@dataclass
class ServerConfig:
    """Server configuration."""

    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    log_level: str = "INFO"


@dataclass
class DatabaseConfig:
    """Database configuration."""

    url: str = "postgresql://localhost/ollama"
    pool_size: int = 20


@dataclass
class OllamaConfig:
    """Main configuration object."""

    server: ServerConfig
    database: DatabaseConfig
    debug: bool = False

    @classmethod
    def from_file(cls, config_path: str) -> "OllamaConfig":
        """Load configuration from YAML file."""
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(path) as f:
            data = yaml.safe_load(f)

        return cls(
            server=ServerConfig(**data.get("server", {})),
            database=DatabaseConfig(**data.get("database", {})),
            debug=data.get("debug", False),
        )

    @classmethod
    def from_env(cls) -> "OllamaConfig":
        """Load configuration from environment variables."""
        config_path = os.getenv("OLLAMA_CONFIG", "config/development.yaml")
        return cls.from_file(config_path)
