"""Model management and generation orchestration."""

from typing import Optional
import structlog

from ollama.services.model import Model
from ollama.services.model_type import ModelType
from ollama.services.generate_request import GenerateRequest
from ollama.services.generate_response import GenerateResponse
from ollama.exceptions.model import ModelNotFoundError

log = structlog.get_logger(__name__)


class OllamaModelManager:
    """Manages model lifecycle and text generation.

    Handles model loading, caching, and orchestrates inference through
    the Ollama backend service.
    """

    def __init__(self, ollama_client: "OllamaClient") -> None:  # type: ignore
        """Initialize model manager with Ollama client.

        Args:
            ollama_client: Client for communicating with Ollama backend.
        """
        self.client = ollama_client
        self._models: dict[str, Model] = {}
        self._model_cache: dict[str, Model] = {}

    async def list_models(self) -> list[Model]:
        """List all available models from Ollama.

        Returns:
            List of available models.

        Raises:
            ModelNotFoundError: If unable to fetch model list.
        """
        log.info("listing_models")
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
            await self.list_models()

        if name not in self._models:
            log.error("model_not_found", model=name)
            raise ModelNotFoundError(f"Model {name} not found")

        model = self._models[name]
        self._model_cache[name] = model
        return model

    async def generate(
        self,
        request: GenerateRequest,
    ) -> GenerateResponse:
        """Generate text using specified model.

        Args:
            request: Generation request with prompt and parameters.

        Returns:
            Generated response with text and metadata.

        Raises:
            ModelNotFoundError: If model not available.
        """
        log.info("generate_request", model=request.model, prompt_len=len(request.prompt))

        # Validate model exists
        await self.get_model(request.model)

        # Call Ollama backend
        response = await self.client.generate(request)

        log.info(
            "generate_complete",
            model=request.model,
            tokens=response.eval_count,
            duration_ms=response.eval_duration // 1_000_000,
        )

        return response

    def clear_cache(self) -> None:
        """Clear in-memory model cache."""
        log.info("clearing_model_cache", models=len(self._model_cache))
        self._model_cache.clear()
