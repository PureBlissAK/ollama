"""Ollama Client Service (backward compatibility).

This module re-exports classes split into individual modules.
For new code, import directly from specific modules.

Legacy imports (deprecated):
    >>> from ollama.services.ollama_client import OllamaClient, ChatMessage, ChatRequest

Preferred imports:
    >>> from ollama.services.ollama_client_main import OllamaClient
    >>> from ollama.services.chat_message import ChatMessage
    >>> from ollama.services.chat_request import ChatRequest
"""

from ollama.services.chat_message import ChatMessage
from ollama.services.chat_request import ChatRequest
from ollama.services.generate_request import GenerateRequest
from ollama.services.ollama_client_main import OllamaClient

# Singleton management for backward compatibility
_ollama_client: OllamaClient | None = None


def init_ollama_client(base_url: str) -> OllamaClient:
    """Initialize and store a global OllamaClient instance.

    Args:
        base_url: Base URL for the Ollama backend service.

    Returns:
        The initialized OllamaClient instance.
    """
    global _ollama_client
    _ollama_client = OllamaClient(base_url=base_url)
    return _ollama_client


def get_ollama_client() -> OllamaClient:
    """Get the global OllamaClient instance.

    Raises:
        RuntimeError: If the client has not been initialized.
    """
    if _ollama_client is None:
        raise RuntimeError("Ollama client not initialized")
    return _ollama_client


__all__ = [
    "ChatMessage",
    "ChatRequest",
    "GenerateRequest",
    "OllamaClient",
    "init_ollama_client",
    "get_ollama_client",
]
