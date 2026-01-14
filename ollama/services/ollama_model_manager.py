"""Model management and generation orchestration."""

from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Any

import structlog

from ollama.exceptions.model import ModelNotFoundError
from ollama.services.generate_request import GenerateRequest
from ollama.services.generate_response import GenerateResponse
from ollama.services.model import Model

if TYPE_CHECKING:
    from ollama.services.ollama_client_main import OllamaClient

log = structlog.get_logger(__name__)


class OllamaModelManager:
    """Manages model lifecycle and text generation.

    Handles model loading, caching, and orchestrates inference through
    the Ollama backend service.
    """

    def __init__(self, ollama_client: "OllamaClient") -> None:
        """Initialize model manager with Ollama client.

        Args:
            ollama_client: Client for communicating with Ollama backend.
        """
        self.client = ollama_client
        self._models: dict[str, Model] = {}
        self._model_cache: dict[str, Model] = {}

    async def list_available_models(self) -> list[Model]:
        """List all available models from Ollama.

        Returns:
            List of available models.

        Raises:
            ModelNotFoundError: If unable to fetch model list.
        """
        log.info("listing_available_models")
        models = await self.client.list_models()
        self._models = {m.name: m for m in models}
        return models

    async def get_model(self, name: str) -> Model:
        """Get specific model by name.

        Args:
            name: Model name (e.g., 'llama2', 'mistral').

        Returns:
            Model information.

        Raises:
            ModelNotFoundError: If model not found.
        """
        if name in self._model_cache:
            return self._model_cache[name]

        if name not in self._models:
            await self.list_available_models()

        if name not in self._models:
            log.error("model_not_found", model=name)
            raise ModelNotFoundError(f"Model {name} not found")

        model = self._models[name]
        self._model_cache[name] = model
        return model

    async def generate(
        self,
        request: GenerateRequest,
    ) -> AsyncGenerator[GenerateResponse, None]:
        """Generate text using specified model.

        Args:
            request: Generation request with prompt and parameters.

        Yields:
            Generated response chunks.
        """
        log.info("generate_request", model=request.model, prompt_len=len(request.prompt))

        # Validate model exists
        await self.get_model(request.model)

        if getattr(request, "stream", False):
            async for chunk in self.client.generate_stream(request):
                yield chunk
        else:
            response = await self.client.generate(request)
            yield response

    async def generate_embedding(self, model_name: str, prompt: str) -> list[float]:
        """Generate embedding for prompt.

        Args:
            model_name: Model to use.
            prompt: Text to embed.

        Returns:
            List of floats.
        """
        await self.get_model(model_name)
        return await self.client.generate_embeddings(model_name, prompt)

    async def pull_model(self, model_name: str) -> dict[str, Any]:
        """Pull model from library.

        Args:
            model_name: Model to pull.

        Returns:
            Success response.
        """
        return await self.client.pull_model(model_name)

    async def delete_model(self, model_name: str) -> None:
        """Delete model.

        Args:
            model_name: Model to delete.
        """
        await self.client.delete_model(model_name)
        if model_name in self._models:
            del self._models[model_name]
        if model_name in self._model_cache:
            del self._model_cache[model_name]

    async def close(self) -> None:
        """Close model manager."""
        await self.client.close()

    def clear_cache(self) -> None:
        """Clear in-memory model cache."""
        log.info("clearing_model_cache", models=len(self._model_cache))
        self._model_cache.clear()
