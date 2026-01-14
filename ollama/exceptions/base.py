"""Base exception hierarchy for Ollama."""


class OllamaError(Exception):
    """Base exception for all Ollama-specific errors."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class AuthenticationError(OllamaError):
    """Base class for authentication errors."""
