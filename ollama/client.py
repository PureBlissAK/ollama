"""Main Ollama client interface."""

from typing import Optional, List, Dict, Any
import httpx


class Client:
    """
    Ollama client for interacting with local inference server.

    Example:
        >>> client = Client(base_url="http://localhost:8000")
        >>> response = client.generate(
        ...     model="llama2",
        ...     prompt="What is AI?",
        ...     stream=False
        ... )
        >>> print(response.text)
    """

    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize Ollama client.

        Args:
            base_url: URL of Ollama server
        """
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(base_url=self.base_url)

    def health(self) -> Dict[str, Any]:
        """Check server health."""
        response = self.client.get("/health")
        response.raise_for_status()
        return response.json()

    def generate(
        self,
        model: str,
        prompt: str,
        stream: bool = False,
        **kwargs: Any,
    ) -> Any:
        """
        Generate text using specified model.

        Args:
            model: Model identifier
            prompt: Input prompt
            stream: Whether to stream output
            **kwargs: Additional parameters

        Returns:
            Generation response
        """
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
            **kwargs,
        }
        response = self.client.post("/api/generate", json=payload)
        response.raise_for_status()
        return response.json()

    def chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        **kwargs: Any,
    ) -> Any:
        """
        Chat interface (OpenAI-compatible).

        Args:
            model: Model identifier
            messages: Chat messages
            **kwargs: Additional parameters

        Returns:
            Chat response
        """
        payload = {
            "model": model,
            "messages": messages,
            **kwargs,
        }
        response = self.client.post("/v1/chat/completions", json=payload)
        response.raise_for_status()
        return response.json()

    def embeddings(
        self,
        model: str,
        input_text: str,
        **kwargs: Any,
    ) -> Any:
        """
        Generate embeddings.

        Args:
            model: Embedding model identifier
            input_text: Text to embed
            **kwargs: Additional parameters

        Returns:
            Embeddings response
        """
        payload = {
            "model": model,
            "input": input_text,
            **kwargs,
        }
        response = self.client.post("/v1/embeddings", json=payload)
        response.raise_for_status()
        return response.json()

    def list_models(self) -> Dict[str, Any]:
        """List available models."""
        response = self.client.get("/api/models")
        response.raise_for_status()
        return response.json()

    def __del__(self):
        """Cleanup client connection."""
        self.client.close()
