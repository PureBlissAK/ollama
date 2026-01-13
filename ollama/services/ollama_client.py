"""
Ollama Client Service - Interface to local Ollama inference engine
Handles model loading, inference, and embeddings generation
"""

import logging
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)

# Global Ollama client instance
_ollama_client: Optional["OllamaClient"] = None


class ChatMessage:
    """Chat message model"""

    def __init__(self, role: str, content: str) -> None:
        """Initialize chat message

        Args:
            role: Message role (user, assistant, system)
            content: Message content
        """
        self.role = role
        self.content = content

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {"role": self.role, "content": self.content}


class ChatRequest:
    """Chat request model"""

    def __init__(
        self,
        model: str,
        messages: list[dict],
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        top_k: Optional[int] = None,
        stream: bool = False,
    ) -> None:
        """Initialize chat request

        Args:
            model: Model name
            messages: List of chat messages
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            top_k: Top-k sampling parameter
            stream: Whether to stream response
        """
        self.model = model
        self.messages = messages
        self.temperature = temperature
        self.top_p = top_p
        self.top_k = top_k
        self.stream = stream

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": self.messages,
            "stream": self.stream,
        }
        if self.temperature is not None:
            payload["temperature"] = self.temperature
        if self.top_p is not None:
            payload["top_p"] = self.top_p
        if self.top_k is not None:
            payload["top_k"] = self.top_k
        return payload


class OllamaClient:
    """Client for Ollama local inference engine"""

    def __init__(self, base_url: str = "http://ollama:11434") -> None:
        """Initialize Ollama client

        Args:
            base_url: Ollama base URL (use 'ollama' Docker service name, NOT localhost)
        """
        self.base_url = base_url
        self.client: Optional[httpx.AsyncClient] = None

    async def initialize(self) -> None:
        """Initialize HTTP client and verify connection"""
        try:
            self.client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)
            # Test connection
            response = await self.client.get("/api/tags")
            if response.status_code != 200:
                raise Exception(f"Ollama server returned status {response.status_code}")
            logger.info(f"Ollama client initialized: {self.base_url}")
        except Exception as e:
            logger.error(f"Failed to initialize Ollama client: {e}")
            raise

    async def close(self) -> None:
        """Close HTTP client"""
        if self.client:
            await self.client.aclose()
            logger.info("Ollama client closed")

    async def list_models(self) -> list[dict]:
        """List available models

        Returns:
            List of available models
        """
        if not self.client:
            return []

        try:
            response = await self.client.get("/api/tags")
            if response.status_code == 200:
                data = response.json()
                return data.get("models", [])
            return []
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []

    async def generate(self, model: str, prompt: str, stream: bool = False) -> Any:
        """Generate text completion

        Args:
            model: Model name
            prompt: Input prompt
            stream: Whether to stream response

        Returns:
            Generation response
        """
        if not self.client:
            raise RuntimeError("Ollama client not initialized")

        try:
            payload = {"model": model, "prompt": prompt, "stream": stream}
            response = await self.client.post("/api/generate", json=payload)
            if response.status_code == 200:
                return response.json() if not stream else response.aiter_lines()
            raise Exception(f"Ollama returned status {response.status_code}")
        except Exception as e:
            logger.error(f"Generate failed: {e}")
            raise

    async def chat(self, model: str, messages: list[dict], stream: bool = False) -> Any:
        """Chat completion

        Args:
            model: Model name
            messages: Chat message history
            stream: Whether to stream response

        Returns:
            Chat response
        """
        if not self.client:
            raise RuntimeError("Ollama client not initialized")

        try:
            payload = {"model": model, "messages": messages, "stream": stream}
            response = await self.client.post("/api/chat", json=payload)
            if response.status_code == 200:
                return response.json() if not stream else response.aiter_lines()
            raise Exception(f"Ollama returned status {response.status_code}")
        except Exception as e:
            logger.error(f"Chat failed: {e}")
            raise

    async def embeddings(self, model: str, text: str) -> list[float]:
        """Generate embeddings

        Args:
            model: Model name
            text: Input text

        Returns:
            Embedding vector
        """
        if not self.client:
            raise RuntimeError("Ollama client not initialized")

        try:
            payload = {"model": model, "prompt": text}
            response = await self.client.post("/api/embeddings", json=payload)
            if response.status_code == 200:
                data = response.json()
                return data.get("embedding", [])
            raise Exception(f"Ollama returned status {response.status_code}")
        except Exception as e:
            logger.error(f"Embeddings failed: {e}")
            raise


def init_ollama_client(base_url: str = "http://ollama:11434") -> OllamaClient:
    """Initialize Ollama client

    Args:
        base_url: Ollama base URL

    Returns:
        Initialized OllamaClient instance
    """
    global _ollama_client
    _ollama_client = OllamaClient(base_url=base_url)
    return _ollama_client


def get_ollama_client() -> Optional[OllamaClient]:
    """Get global Ollama client instance

    Returns:
        Global OllamaClient or None if not initialized
    """
    return _ollama_client
