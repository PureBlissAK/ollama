"""Dependency injection for API routes.

Provides FastAPI dependency functions for managing services and
database connections across request lifecycle.
"""

import logging

from ollama.services.ollama_model_manager import OllamaModelManager

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
    from ollama.services.ollama_client_main import OllamaClient

    client = OllamaClient(base_url=base_url)
    _model_manager = OllamaModelManager(ollama_client=client)
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
