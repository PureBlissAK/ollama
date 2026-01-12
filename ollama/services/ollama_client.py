"""
Ollama HTTP Client - Direct integration with Ollama inference engine
Provides async methods for model management, text generation, and chat
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, AsyncIterator
from urllib.parse import urljoin

import httpx
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class OllamaModel(BaseModel):
    """Ollama model information"""
    name: str
    size: Optional[int] = None
    digest: Optional[str] = None
    modified_at: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class GenerateRequest(BaseModel):
    """Generate request parameters"""
    model: str
    prompt: str
    stream: bool = Field(default=False)
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(default=0.9, ge=0.0, le=1.0)
    top_k: Optional[int] = Field(default=40, ge=0)
    num_predict: Optional[int] = Field(default=None, ge=-1)
    stop: Optional[List[str]] = None
    context: Optional[List[int]] = None


class ChatMessage(BaseModel):
    """Chat message"""
    role: str  # system, user, assistant
    content: str


class ChatRequest(BaseModel):
    """Chat request parameters"""
    model: str
    messages: List[ChatMessage]
    stream: bool = Field(default=False)
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(default=0.9, ge=0.0, le=1.0)
    top_k: Optional[int] = Field(default=40, ge=0)


class EmbeddingRequest(BaseModel):
    """Embedding request parameters"""
    model: str
    prompt: str


class OllamaClient:
    """
    Async HTTP client for Ollama inference engine
    
    Provides methods for:
    - Model management (list, show, pull, delete)
    - Text generation (streaming and non-streaming)
    - Chat completion (OpenAI-compatible)
    - Embeddings generation
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        timeout: float = 300.0,
        connect_timeout: float = 10.0
    ):
        """
        Initialize Ollama client
        
        Args:
            base_url: Ollama server base URL
            timeout: Request timeout in seconds
            connect_timeout: Connection timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = httpx.Timeout(timeout, connect=connect_timeout)
        self._client: Optional[httpx.AsyncClient] = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize HTTP client and test connection"""
        try:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                follow_redirects=True
            )
            
            # Test connection
            response = await self._client.get("/api/tags")
            response.raise_for_status()
            
            self._initialized = True
            logger.info(f"✅ Ollama client connected to {self.base_url}")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to Ollama: {e}")
            raise ConnectionError(f"Cannot connect to Ollama at {self.base_url}: {e}")
    
    async def close(self):
        """Close HTTP client"""
        if self._client:
            await self._client.aclose()
            logger.info("✅ Ollama client connection closed")
    
    async def list_models(self) -> List[OllamaModel]:
        """
        List available models
        
        Returns:
            List of OllamaModel objects
        """
        if not self._initialized:
            raise RuntimeError("Client not initialized. Call initialize() first.")
        
        response = await self._client.get("/api/tags")
        response.raise_for_status()
        data = response.json()
        
        models = []
        for model_data in data.get("models", []):
            models.append(OllamaModel(**model_data))
        
        return models
    
    async def show_model(self, name: str) -> Dict[str, Any]:
        """
        Get detailed information about a model
        
        Args:
            name: Model name
            
        Returns:
            Model details dictionary
        """
        if not self._initialized:
            raise RuntimeError("Client not initialized. Call initialize() first.")
        
        response = await self._client.post(
            "/api/show",
            json={"name": name}
        )
        response.raise_for_status()
        return response.json()
    
    async def generate(
        self,
        request: GenerateRequest
    ) -> Dict[str, Any]:
        """
        Generate text from prompt (non-streaming)
        
        Args:
            request: GenerateRequest with model and prompt
            
        Returns:
            Response dictionary with generated text
        """
        if not self._initialized:
            raise RuntimeError("Client not initialized. Call initialize() first.")
        
        response = await self._client.post(
            "/api/generate",
            json=request.model_dump(exclude_none=True)
        )
        response.raise_for_status()
        return response.json()
    
    async def generate_stream(
        self,
        request: GenerateRequest
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Generate text with streaming response
        
        Args:
            request: GenerateRequest with stream=True
            
        Yields:
            Response chunks as they arrive
        """
        if not self._initialized:
            raise RuntimeError("Client not initialized. Call initialize() first.")
        
        request.stream = True
        
        async with self._client.stream(
            "POST",
            "/api/generate",
            json=request.model_dump(exclude_none=True)
        ) as response:
            response.raise_for_status()
            
            async for line in response.aiter_lines():
                if line.strip():
                    import json
                    yield json.loads(line)
    
    async def chat(
        self,
        request: ChatRequest
    ) -> Dict[str, Any]:
        """
        Chat completion (non-streaming)
        
        Args:
            request: ChatRequest with messages
            
        Returns:
            Response dictionary with assistant message
        """
        if not self._initialized:
            raise RuntimeError("Client not initialized. Call initialize() first.")
        
        # Convert messages to dict format
        messages_dict = [msg.model_dump() for msg in request.messages]
        
        payload = {
            "model": request.model,
            "messages": messages_dict,
            "stream": False
        }
        
        if request.temperature is not None:
            payload["temperature"] = request.temperature
        if request.top_p is not None:
            payload["top_p"] = request.top_p
        if request.top_k is not None:
            payload["top_k"] = request.top_k
        
        response = await self._client.post("/api/chat", json=payload)
        response.raise_for_status()
        return response.json()
    
    async def chat_stream(
        self,
        request: ChatRequest
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Chat completion with streaming
        
        Args:
            request: ChatRequest with stream=True
            
        Yields:
            Response chunks as they arrive
        """
        if not self._initialized:
            raise RuntimeError("Client not initialized. Call initialize() first.")
        
        messages_dict = [msg.model_dump() for msg in request.messages]
        
        payload = {
            "model": request.model,
            "messages": messages_dict,
            "stream": True
        }
        
        if request.temperature is not None:
            payload["temperature"] = request.temperature
        if request.top_p is not None:
            payload["top_p"] = request.top_p
        if request.top_k is not None:
            payload["top_k"] = request.top_k
        
        async with self._client.stream("POST", "/api/chat", json=payload) as response:
            response.raise_for_status()
            
            async for line in response.aiter_lines():
                if line.strip():
                    import json
                    yield json.loads(line)
    
    async def embeddings(
        self,
        request: EmbeddingRequest
    ) -> Dict[str, Any]:
        """
        Generate embeddings for text
        
        Args:
            request: EmbeddingRequest with model and prompt
            
        Returns:
            Response with embedding vector
        """
        if not self._initialized:
            raise RuntimeError("Client not initialized. Call initialize() first.")
        
        response = await self._client.post(
            "/api/embeddings",
            json=request.model_dump()
        )
        response.raise_for_status()
        return response.json()
    
    async def pull_model(self, name: str) -> AsyncIterator[Dict[str, Any]]:
        """
        Pull/download a model (streaming progress)
        
        Args:
            name: Model name to pull
            
        Yields:
            Progress updates
        """
        if not self._initialized:
            raise RuntimeError("Client not initialized. Call initialize() first.")
        
        async with self._client.stream(
            "POST",
            "/api/pull",
            json={"name": name}
        ) as response:
            response.raise_for_status()
            
            async for line in response.aiter_lines():
                if line.strip():
                    import json
                    yield json.loads(line)
    
    async def delete_model(self, name: str) -> Dict[str, Any]:
        """
        Delete a model
        
        Args:
            name: Model name to delete
            
        Returns:
            Deletion confirmation
        """
        if not self._initialized:
            raise RuntimeError("Client not initialized. Call initialize() first.")
        
        response = await self._client.delete(
            "/api/delete",
            json={"name": name}
        )
        response.raise_for_status()
        return response.json()


# Global client instance
_ollama_client: Optional[OllamaClient] = None


def init_ollama_client(
    base_url: str = "http://localhost:11434",
    timeout: float = 300.0,
    connect_timeout: float = 10.0
) -> OllamaClient:
    """
    Initialize global Ollama client
    
    Args:
        base_url: Ollama server URL
        timeout: Request timeout
        connect_timeout: Connection timeout
        
    Returns:
        Initialized OllamaClient instance
    """
    global _ollama_client
    _ollama_client = OllamaClient(base_url, timeout, connect_timeout)
    return _ollama_client


def get_ollama_client() -> OllamaClient:
    """
    Get global Ollama client instance
    
    Returns:
        OllamaClient instance
        
    Raises:
        RuntimeError: If client not initialized
    """
    if _ollama_client is None:
        raise RuntimeError("Ollama client not initialized")
    return _ollama_client
