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
from ollama.services.ollama_client_main import OllamaClient

__all__ = [
    "ChatMessage",
    "ChatRequest",
    "OllamaClient",
]
