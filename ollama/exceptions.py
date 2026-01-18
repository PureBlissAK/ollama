"""Custom exception hierarchy for Ollama API.

Provides structured exception types for different error scenarios
with proper context and logging integration.
"""

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class OllamaException(Exception):
    """Base exception for all Ollama-specific errors.

    Attributes:
        code: Machine-readable error code
        message: Human-readable error message
        status_code: HTTP status code
        details: Additional error context
    """

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 500,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        """Initialize Ollama exception.

        Args:
            code: Machine-readable error code (e.g., 'MODEL_NOT_FOUND')
            message: Human-readable error message
            status_code: HTTP status code (default: 500)
            details: Additional error context dictionary
        """
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to API response dictionary.

        Returns:
            Dictionary with error details for JSON response
        """
        return {
            "success": False,
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
            },
        }

    def log(self, level: int = logging.ERROR) -> None:
        """Log exception with context.

        Args:
            level: Logging level (default: ERROR)
        """
        logger.log(
            level,
            f"{self.code}: {self.message}",
            extra={"details": self.details},
        )


# Model-related exceptions


class ModelNotFoundError(OllamaException):
    """Model not found or not available.

    Attributes:
        model_name: Name of the model that was not found
    """

    def __init__(self, model_name: str) -> None:
        """Initialize model not found exception.

        Args:
            model_name: Name of the missing model
        """
        self.model_name = model_name
        super().__init__(
            code="MODEL_NOT_FOUND",
            message=f"Model '{model_name}' not found",
            status_code=404,
            details={"model": model_name},
        )


class ModelLoadError(OllamaException):
    """Error loading or initializing model.

    Attributes:
        model_name: Name of the model
        reason: Reason for load failure
    """

    def __init__(self, model_name: str, reason: str) -> None:
        """Initialize model load error.

        Args:
            model_name: Name of the model
            reason: Reason for load failure
        """
        self.model_name = model_name
        self.reason = reason
        super().__init__(
            code="MODEL_LOAD_ERROR",
            message=f"Failed to load model '{model_name}': {reason}",
            status_code=503,
            details={"model": model_name, "reason": reason},
        )


# Inference-related exceptions


class InferenceError(OllamaException):
    """Error during model inference."""

    def __init__(self, message: str, model: Optional[str] = None) -> None:
        """Initialize inference error.

        Args:
            message: Error message
            model: Optional model name
        """
        super().__init__(
            code="INFERENCE_ERROR",
            message=message,
            status_code=500,
            details={"model": model} if model else {},
        )


class InferenceTimeoutError(OllamaException):
    """Inference request timed out.

    Attributes:
        elapsed_ms: Time elapsed in milliseconds
        timeout_ms: Timeout threshold in milliseconds
    """

    def __init__(self, elapsed_ms: float, timeout_ms: int) -> None:
        """Initialize inference timeout error.

        Args:
            elapsed_ms: Time elapsed in milliseconds
            timeout_ms: Timeout threshold in milliseconds
        """
        self.elapsed_ms = elapsed_ms
        self.timeout_ms = timeout_ms
        super().__init__(
            code="INFERENCE_TIMEOUT",
            message=f"Inference timed out after {elapsed_ms:.1f}ms (limit: {timeout_ms}ms)",
            status_code=504,
            details={"elapsed_ms": elapsed_ms, "timeout_ms": timeout_ms},
        )


class InvalidPromptError(OllamaException):
    """Invalid or malformed prompt."""

    def __init__(self, reason: str) -> None:
        """Initialize invalid prompt error.

        Args:
            reason: Reason why prompt is invalid
        """
        super().__init__(
            code="INVALID_PROMPT",
            message=f"Invalid prompt: {reason}",
            status_code=400,
            details={"reason": reason},
        )


# Authentication exceptions


class AuthenticationError(OllamaException):
    """Authentication failed."""

    def __init__(self, reason: str = "Invalid credentials") -> None:
        """Initialize authentication error.

        Args:
            reason: Reason for authentication failure
        """
        super().__init__(
            code="AUTHENTICATION_ERROR",
            message=reason,
            status_code=401,
            details={"reason": reason},
        )


class APIKeyInvalidError(OllamaException):
    """API key is invalid or expired."""

    def __init__(self) -> None:
        """Initialize invalid API key error."""
        super().__init__(
            code="INVALID_API_KEY",
            message="API key is invalid or expired",
            status_code=401,
        )


# Rate limiting exceptions


class RateLimitExceededError(OllamaException):
    """Rate limit exceeded.

    Attributes:
        limit: Request limit
        window: Time window (seconds)
        retry_after: Seconds to wait before retrying
    """

    def __init__(
        self, limit: int, window: int, retry_after: int
    ) -> None:
        """Initialize rate limit exceeded error.

        Args:
            limit: Request limit
            window: Time window in seconds
            retry_after: Seconds to wait before retrying
        """
        self.limit = limit
        self.window = window
        self.retry_after = retry_after
        super().__init__(
            code="RATE_LIMIT_EXCEEDED",
            message=f"Rate limit exceeded ({limit} requests per {window}s)",
            status_code=429,
            details={
                "limit": limit,
                "window": window,
                "retry_after": retry_after,
            },
        )


# Resource exceptions


class ResourceNotFoundError(OllamaException):
    """Resource not found."""

    def __init__(self, resource_type: str, resource_id: str) -> None:
        """Initialize resource not found error.

        Args:
            resource_type: Type of resource (e.g., 'conversation')
            resource_id: ID of the resource
        """
        super().__init__(
            code="RESOURCE_NOT_FOUND",
            message=f"{resource_type} '{resource_id}' not found",
            status_code=404,
            details={
                "resource_type": resource_type,
                "resource_id": resource_id,
            },
        )


class ValidationError(OllamaException):
    """Input validation failed."""

    def __init__(self, field: str, reason: str) -> None:
        """Initialize validation error.

        Args:
            field: Field that failed validation
            reason: Reason for validation failure
        """
        super().__init__(
            code="VALIDATION_ERROR",
            message=f"Validation failed for field '{field}': {reason}",
            status_code=400,
            details={"field": field, "reason": reason},
        )


# Database exceptions


class DatabaseError(OllamaException):
    """Database operation failed."""

    def __init__(self, operation: str, reason: str) -> None:
        """Initialize database error.

        Args:
            operation: Database operation that failed
            reason: Reason for failure
        """
        super().__init__(
            code="DATABASE_ERROR",
            message=f"Database {operation} failed: {reason}",
            status_code=500,
            details={"operation": operation, "reason": reason},
        )


# Configuration exceptions


class ConfigurationError(OllamaException):
    """Configuration error."""

    def __init__(self, setting: str, reason: str) -> None:
        """Initialize configuration error.

        Args:
            setting: Configuration setting that is invalid
            reason: Reason for configuration error
        """
        super().__init__(
            code="CONFIGURATION_ERROR",
            message=f"Configuration error for '{setting}': {reason}",
            status_code=500,
            details={"setting": setting, "reason": reason},
        )
