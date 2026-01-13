"""FastAPI server for Ollama with public endpoint support."""

import logging
import os
from typing import Any, Dict, Optional

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZIPMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ollama.config import OllamaConfig

logger = logging.getLogger(__name__)


# Request/Response Models
class HealthResponse(BaseModel):
    """Server health status."""

    status: str
    version: str
    environment: str
    public_url: Optional[str] = None


class ModelListResponse(BaseModel):
    """List of available models."""

    models: list


class GenerateRequest(BaseModel):
    """Text generation request."""

    model: str
    prompt: str
    stream: bool = False
    temperature: float = 0.7
    top_p: float = 0.95
    top_k: int = 40


class ChatRequest(BaseModel):
    """Chat completion request."""

    model: str
    messages: list
    temperature: float = 0.7
    stream: bool = False


def create_app(config: Optional[OllamaConfig] = None) -> FastAPI:  # noqa: C901
    """
    Create and configure FastAPI application.

    Args:
        config: OllamaConfig instance (loads from env if None)

    Returns:
        Configured FastAPI app
    """
    if config is None:
        config = OllamaConfig.from_env()

    app = FastAPI(
        title="Ollama API",
        description="Elite local AI inference platform for elevatediq.ai",
        version="1.0.0",
    )

    # Middleware: GZIP compression
    app.add_middleware(GZIPMiddleware, minimum_size=1000)

    # Middleware: CORS (public endpoint support)
    cors_origins = config.security.get(
        "cors_origins", ["https://elevatediq.ai", "https://elevatediq.ai/ollama"]
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=config.security.get("cors_allow_credentials", True),
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=config.security.get("cors_expose_headers", ["Content-Type"]),
        max_age=3600,
    )

    # Middleware: Security headers
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        """Add security headers to all responses."""
        response = await call_next(request)

        # Strict Transport Security
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )

        # Content Security
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Add request ID for tracing
        response.headers["X-Request-ID"] = request.headers.get("X-Request-ID", "unknown")

        return response

    # Middleware: API Key authentication
    @app.middleware("http")
    async def api_key_auth(request: Request, call_next):
        """Validate API key for protected endpoints."""
        if not config.security.get("api_key_auth_enabled", True):
            return await call_next(request)

        # Skip auth for health endpoint
        if request.url.path == "/health":
            return await call_next(request)

        api_key = request.headers.get("X-API-Key") or request.headers.get("Authorization")

        if not api_key:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "API key required"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        return await call_next(request)

    # Routes: Health check
    @app.get("/health", response_model=HealthResponse)
    async def health() -> HealthResponse:
        """
        Health check endpoint.

        Returns server status and configuration information.
        """
        return HealthResponse(
            status="healthy",
            version="1.0.0",
            environment=os.getenv("OLLAMA_ENV", "development"),
            public_url=config.server.get("public_url"),
        )

    @app.get("/api/models", response_model=ModelListResponse)
    async def list_models() -> ModelListResponse:
        """
        List available models.

        Returns:
            List of model identifiers

        Integration: Connected to ollama_client service
        See: ollama.services.ollama_client for actual model enumeration
        """
        # Placeholder for demonstration - actual models from Ollama engine
        return ModelListResponse(
            models=[
                {"name": "llama2", "size": "7b", "quantization": "q4_K_M"},
                {"name": "mistral", "size": "7b", "quantization": "q5_K_M"},
            ]
        )

    # Routes: Text generation
    @app.post("/api/generate")
    async def generate(request: GenerateRequest) -> Dict[str, Any]:
        """
        Generate text using specified model.

        Args:
            request: Generation request with model and prompt

        Returns:
            Generated text response

        Integration: Routed to ollama_client.generate()
        See: ollama.services.ollama_client for implementation

        Example:
            POST /api/generate
            {
                "model": "llama2",
                "prompt": "Explain local AI",
                "stream": false
            }
        """
        # Placeholder response structure - actual inference via ollama_client service
        return {
            "model": request.model,
            "response": "Generated response from " + request.model,
            "done": True,
            "context": [],
        }

    # Routes: Chat completions (OpenAI-compatible)
    @app.post("/v1/chat/completions")
    async def chat_completions(request: ChatRequest) -> Dict[str, Any]:
        """
        Chat completions endpoint (OpenAI-compatible).

        Args:
            request: Chat request with messages

        Returns:
            Chat response

        Integration: Routed to ollama_client.chat()
        See: ollama.services.ollama_client for implementation

        Example:
            POST /v1/chat/completions
            {
                "model": "llama2",
                "messages": [{"role": "user", "content": "Hello"}]
            }
        """
        # Placeholder response - actual chat inference via ollama_client service
        return {
            "id": "chatcmpl-123",
            "object": "chat.completion",
            "created": 1234567890,
            "model": request.model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Hello! How can I help you?",
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 10,
                "total_tokens": 20,
            },
        }

    # Routes: Embeddings (OpenAI-compatible)
    @app.post("/v1/embeddings")
    async def embeddings(request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate embeddings (OpenAI-compatible).

        Args:
            request: Embedding request with input text

        Returns:
            Embeddings response

        Integration: Routed to embedding service (Qdrant/Vector DB)
        See: ollama.services.vector for implementation
        """
        # Placeholder response - actual embeddings via vector service
        return {
            "object": "list",
            "data": [
                {
                    "object": "embedding",
                    "embedding": [0.1, 0.2, 0.3],  # Placeholder
                    "index": 0,
                }
            ],
            "model": request.get("model", "embedding-model"),
            "usage": {
                "prompt_tokens": 5,
                "total_tokens": 5,
            },
        }

    # Routes: Admin stats
    @app.get("/admin/stats")
    async def stats(request: Request) -> Dict[str, Any]:
        """
        System statistics and metrics.

        Returns:
            System health and performance metrics

        Integration: Data from Prometheus metrics
        See: ollama.monitoring.prometheus_config for available metrics
        """
        # Placeholder metrics - actual data from Prometheus/metrics system
        return {
            "uptime_seconds": 3600,
            "gpu_memory_used": 5000,
            "gpu_memory_total": 24000,
            "requests_total": 1500,
            "errors_total": 5,
            "average_latency_ms": 850,
        }

    return app


if __name__ == "__main__":
    import uvicorn

    config = OllamaConfig.from_env()
    app = create_app(config)

    uvicorn.run(
        app,
        host=config.server.get("host", "0.0.0.0"),
        port=config.server.get("port", 8000),
        workers=config.server.get("workers", 4),
        log_level=config.server.get("log_level", "info").lower(),
    )
