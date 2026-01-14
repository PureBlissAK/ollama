"""Ollama model management and integration.

This module provides interfaces for managing and interacting with Ollama
models running locally on Docker. Handles model loading, inference, and
streaming responses.

Example:
    >>> from ollama.services.models import OllamaModelManager
    >>> manager = OllamaModelManager()
    >>> models = await manager.list_available_models()
    >>> for model in models:
    ...     print(f"Model: {model.name} ({model.size})")
"""

from typing import AsyncGenerator, Optional
from dataclasses import dataclass
from enum import Enum
import logging

import httpx

log = logging.getLogger(__name__)


class ModelType(str, Enum):
    """Types of available Ollama models."""

    TEXT_GENERATION = "text_generation"
    EMBEDDING = "embedding"
    CHAT = "chat"


@dataclass
class Model:
    """Represents an available Ollama model."""

    name: str
    """Model identifier (e.g., 'llama2:latest', 'mistral:7b')"""

    size: str
    """Model size in human-readable format (e.g., '3.8GB')"""

    model_type: ModelType
    """Type of model (text generation, embedding, etc.)"""

    description: str
    """Human-friendly model description"""

    parameters: int
    """Number of parameters in the model"""

    context_length: int
    """Context window size in tokens"""

    quantization: str
    """Quantization level (e.g., '4bit', '8bit', 'float16')"""

    loaded: bool = False
    """Whether model is currently loaded in memory"""


@dataclass
class GenerateRequest:
    """Request for text generation."""

    model: str
    """Model name to use for generation"""

    prompt: str
    """Input prompt for generation"""

    system: Optional[str] = None
    """System prompt to set context"""

    temperature: float = 0.7
    """Sampling temperature (0.0 to 2.0)"""

    top_p: float = 0.9
    """Nucleus sampling parameter"""

    top_k: int = 40
    """Top-K sampling parameter"""

    repeat_penalty: float = 1.1
    """Penalty for repetition"""

    num_predict: int = 100
    """Maximum tokens to generate"""

    context_length: int = 2048
    """Context window size"""

    stream: bool = False
    """Whether to stream response"""


@dataclass
class GenerateResponse:
    """Response from text generation."""

    model: str
    """Model used for generation"""

    prompt: str
    """Original prompt"""

    response: str
    """Generated text"""

    done: bool = True
    """Whether generation is complete"""

    context: list[int] = None
    """Context tokens for continuation"""

    total_duration: int = 0
    """Total generation time in nanoseconds"""

    load_duration: int = 0
    """Time to load model in nanoseconds"""

    prompt_eval_count: int = 0
    """Number of prompt tokens evaluated"""

    prompt_eval_duration: int = 0
    """Time to evaluate prompt in nanoseconds"""

    eval_count: int = 0
    """Number of tokens generated"""

    eval_duration: int = 0
    """Time to generate tokens in nanoseconds"""


class OllamaModelManager:
    """Manages Ollama models and inference operations.

    Interfaces with Ollama service running on Docker to provide model
    management, inference, and streaming capabilities.
    """

    def __init__(self, base_url: str = "http://ollama:11434") -> None:
        """Initialize model manager.

        Args:
            base_url: Base URL for Ollama service
        """
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=600.0)

    async def close(self) -> None:
        """Close HTTP client connection."""
        await self.client.aclose()

    async def list_available_models(self) -> list[Model]:
        """List all available Ollama models.

        Returns:
            List of available models with metadata

        Raises:
            httpx.HTTPError: If connection to Ollama fails
        """
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            data = response.json()

            models: list[Model] = []
            for model_data in data.get("models", []):
                model = Model(
                    name=model_data.get("name"),
                    size=model_data.get("size"),
                    model_type=ModelType.TEXT_GENERATION,  # Default
                    description=f"Ollama model: {model_data.get('name')}",
                    parameters=model_data.get("parameters", 0),
                    context_length=model_data.get("context_length", 2048),
                    quantization=model_data.get("quantization", "unknown"),
                    loaded=model_data.get("loaded", False),
                )
                models.append(model)

            log.info(f"Found {len(models)} available models")
            return models

        except httpx.RequestError as e:
            log.error(f"Failed to connect to Ollama: {e}")
            raise

    async def generate(
        self, request: GenerateRequest
    ) -> AsyncGenerator[GenerateResponse, None]:
        """Generate text using specified model with streaming.

        Args:
            request: Generation request with model and parameters

        Yields:
            Partial generation responses as tokens are generated

        Raises:
            httpx.HTTPError: If connection to Ollama fails
            ValueError: If model not found
        """
        try:
            payload = {
                "model": request.model,
                "prompt": request.prompt,
                "temperature": request.temperature,
                "top_p": request.top_p,
                "top_k": request.top_k,
                "repeat_penalty": request.repeat_penalty,
                "num_predict": request.num_predict,
                "stream": True,
            }

            if request.system:
                payload["system"] = request.system

            log.info(
                f"Generating text with model {request.model}: "
                f"{request.prompt[:50]}..."
            )

            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json=payload,
            )
            response.raise_for_status()

            full_response = ""
            async for line in response.aiter_lines():
                if line:
                    import json

                    try:
                        chunk = json.loads(line)
                        full_response += chunk.get("response", "")

                        yield GenerateResponse(
                            model=chunk.get("model", request.model),
                            prompt=request.prompt,
                            response=chunk.get("response", ""),
                            done=chunk.get("done", False),
                            context=chunk.get("context", []),
                            total_duration=chunk.get("total_duration", 0),
                            load_duration=chunk.get("load_duration", 0),
                            prompt_eval_count=chunk.get("prompt_eval_count", 0),
                            prompt_eval_duration=chunk.get("prompt_eval_duration", 0),
                            eval_count=chunk.get("eval_count", 0),
                            eval_duration=chunk.get("eval_duration", 0),
                        )
                    except Exception as e:
                        log.error(f"Error parsing Ollama response: {e}")
                        continue

        except httpx.RequestError as e:
            log.error(f"Generation failed: {e}")
            raise

    async def generate_embedding(self, text: str, model: str = "nomic-embed-text") -> list[float]:
        """Generate embeddings for text.

        Args:
            text: Text to embed
            model: Embedding model to use

        Returns:
            Vector embedding as list of floats

        Raises:
            httpx.HTTPError: If connection to Ollama fails
        """
        try:
            response = await self.client.post(
                f"{self.base_url}/api/embeddings",
                json={"model": model, "prompt": text},
            )
            response.raise_for_status()
            data = response.json()
            return data.get("embedding", [])

        except httpx.RequestError as e:
            log.error(f"Embedding generation failed: {e}")
            raise

    async def pull_model(self, model_name: str) -> None:
        """Download and prepare a model.

        Args:
            model_name: Model identifier (e.g., 'llama2:latest')

        Raises:
            httpx.HTTPError: If pull operation fails
        """
        try:
            log.info(f"Pulling model: {model_name}")
            response = await self.client.post(
                f"{self.base_url}/api/pull",
                json={"name": model_name},
                timeout=1800.0,  # 30 minute timeout for downloads
            )
            response.raise_for_status()
            log.info(f"Successfully pulled model: {model_name}")

        except httpx.RequestError as e:
            log.error(f"Model pull failed: {e}")
            raise

    async def delete_model(self, model_name: str) -> None:
        """Remove a model from storage.

        Args:
            model_name: Model identifier to delete

        Raises:
            httpx.HTTPError: If delete operation fails
        """
        try:
            log.info(f"Deleting model: {model_name}")
            response = await self.client.delete(
                f"{self.base_url}/api/delete",
                json={"name": model_name},
            )
            response.raise_for_status()
            log.info(f"Successfully deleted model: {model_name}")

        except httpx.RequestError as e:
            log.error(f"Model delete failed: {e}")
            raise
