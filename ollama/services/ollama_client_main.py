"""Ollama API client for model inference."""

from types import TracebackType
from typing import Any

import httpx
import structlog

from ollama.services.chat_message import ChatMessage
from ollama.services.chat_request import ChatRequest
from ollama.services.generate_request import GenerateRequest
from ollama.services.generate_response import GenerateResponse
from ollama.services.model import Model
from ollama.services.model_type import ModelType

log: Any = structlog.get_logger(__name__)


class OllamaClient:
    """HTTP client for Ollama API.

    Communicates with local Ollama backend service for model inference,
    model management, and embedding generation.
    """

    def __init__(self, base_url: str = "http://localhost:11434") -> None:
        """Initialize Ollama client.

        Args:
            base_url: Base URL for Ollama API (default: localhost:11434).
        """
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(60.0),
        )

    async def initialize(self) -> None:
        """Initialize client by performing a lightweight health check.

        This ensures connectivity to the Ollama backend. It's safe to call even if
        the backend is unavailable; exceptions should be handled by callers.
        """
        # Perform a simple request to validate the base URL; ignore response content
        try:
            resp = await self.client.get("/api/tags")
            resp.raise_for_status()
        except httpx.HTTPError:
            # Defer handling to caller; this method is for connectivity warmup
            pass

    async def list_models(self) -> list[Model]:
        """List all available models on Ollama server.

        Returns:
            List of available models with metadata.

        Raises:
            httpx.HTTPError: If API request fails.
        """
        log.info("ollama_list_models", endpoint=self.base_url)

        response = await self.client.get("/api/tags")
        response.raise_for_status()

        data = response.json()
        models: list[Model] = [
            Model(
                name=m.get("name", "unknown"),
                size=str(m.get("size", "")),
                model_type=ModelType.TEXT_GENERATION,
                description=m.get("details", {}).get("description", ""),
                parameters=int(m.get("parameters", 0) or 0),
                context_length=int(m.get("context_length", 0) or 0),
                quantization=m.get("quantization", ""),
                loaded=bool(m.get("loaded", False)),
            )
            for m in data.get("models", [])
        ]

        log.info("ollama_models_listed", count=len(models))
        return models

    async def generate(self, request: GenerateRequest) -> GenerateResponse:
        """Generate text completion.

        Args:
            request: Generation request with prompt and parameters.

        Returns:
            Generated response with text and timing information.

        Raises:
            httpx.HTTPError: If API request fails.
        """
        log.info("ollama_generate", model=request.model, prompt_len=len(request.prompt))

        payload: dict[str, Any] = {
            "model": request.model,
            "prompt": request.prompt,
            "temperature": request.temperature,
            "top_p": request.top_p,
            "top_k": request.top_k,
            "num_predict": request.num_predict,
            "stop": request.stop,
            "stream": False,
        }

        response = await self.client.post("/api/generate", json=payload)
        response.raise_for_status()

        data = response.json()

        return GenerateResponse(
            model=data["model"],
            prompt=request.prompt,
            response=data["response"],
            done=data.get("done", True),
            context=data.get("context", []),
            total_duration=data.get("total_duration", 0),
            load_duration=data.get("load_duration", 0),
            prompt_eval_count=data.get("prompt_eval_count", 0),
            prompt_eval_duration=data.get("prompt_eval_duration", 0),
            eval_count=data.get("eval_count", 0),
            eval_duration=data.get("eval_duration", 0),
        )

    async def chat(self, request: ChatRequest) -> ChatMessage:
        """Generate chat response.

        Args:
            request: Chat request with messages and parameters.

        Returns:
            Chat response message from assistant.

        Raises:
            httpx.HTTPError: If API request fails.
        """
        log.info("ollama_chat", model=request.model, messages=len(request.messages))

        messages = [{"role": m.role, "content": m.content} for m in request.messages]

        payload: dict[str, Any] = {
            "model": request.model,
            "messages": messages,
            "temperature": request.temperature,
            "top_p": request.top_p,
            "top_k": request.top_k,
            "num_predict": request.num_predict,
            "stream": False,
        }

        response = await self.client.post("/api/chat", json=payload)
        response.raise_for_status()

        data = response.json()
        message = data["message"]

        return ChatMessage(role=message["role"], content=message["content"])

    async def close(self) -> None:
        """Close HTTP client connection."""
        await self.client.aclose()

    async def __aenter__(self) -> "OllamaClient":
        """Async context manager entry."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Async context manager exit."""
        await self.close()
