"""Dependency injection for API routes.

Provides FastAPI dependency functions for managing services and
database connections across request lifecycle.
"""

import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from ollama.database import get_async_session
from ollama.services.models import OllamaModelManager

log = logging.getLogger(__name__)

# Global model manager instance
_model_manager: OllamaModelManager | None = None


def initialize_model_manager(base_url: str = "http://ollama:11434") -> None:
    """Initialize the global model manager.

    Should be called during application startup.

    Args:
        base_url: Base URL for Ollama service
    """
    global _model_manager
    _model_manager = OllamaModelManager(base_url=base_url)
    log.info(f"Model manager initialized with base URL: {base_url}")


async def close_model_manager() -> None:
    """Close the model manager connection.

    Should be called during application shutdown.
    """
    global _model_manager
    if _model_manager:
        await _model_manager.close()
        log.info("Model manager closed")


async def get_model_manager() -> OllamaModelManager:
    """Get the model manager instance.

    Used as a FastAPI dependency to provide model manager to routes.

    Returns:
        OllamaModelManager instance

    Raises:
        RuntimeError: If manager not initialized
    """
    if _model_manager is None:
        raise RuntimeError("Model manager not initialized")
    return _model_manager


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session as async generator.

    Used as a FastAPI dependency to provide database sessions to routes.
    Automatically handles session cleanup.

    Yields:
        AsyncSession for database operations
    """
    async with get_async_session() as session:
        yield session
