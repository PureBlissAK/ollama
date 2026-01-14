"""Ollama inference API routes.

Provides endpoints for text generation, embeddings, model management,
and conversation history with streaming support.
"""

from typing import AsyncGenerator
import logging

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from starlette.responses import StreamingResponse

from ollama.services.models import (
    OllamaModelManager,
    GenerateRequest as OllamaGenerateRequest,
    Model,
)
from ollama.api.dependencies import get_model_manager

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["inference"])


# Request/Response Schemas
class ListModelsResponse(BaseModel):
    """Response containing available models."""

    models: list[Model]
    """List of available models"""

    total: int
    """Total number of models"""


class GenerateRequest(BaseModel):
    """Request for text generation."""

    model: str = Field(..., description="Model name (e.g., 'llama2:latest')")
    prompt: str = Field(..., description="Input prompt for generation")
    system: str | None = Field(None, description="System prompt for context")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")
    top_p: float = Field(0.9, ge=0.0, le=1.0, description="Nucleus sampling")
    top_k: int = Field(40, ge=1, description="Top-K sampling")
    repeat_penalty: float = Field(1.1, ge=0.0, description="Repetition penalty")
    num_predict: int = Field(100, ge=1, le=4096, description="Max tokens to generate")
    stream: bool = Field(True, description="Stream response tokens")


class GenerateResponse(BaseModel):
    """Response from text generation."""

    model: str
    """Model used for generation"""

    prompt: str
    """Original prompt"""

    response: str
    """Generated text"""

    done: bool
    """Whether generation is complete"""

    total_duration: int
    """Total generation time (nanoseconds)"""

    prompt_eval_count: int
    """Tokens in prompt"""

    eval_count: int
    """Tokens generated"""


class EmbeddingRequest(BaseModel):
    """Request for text embedding."""

    text: str = Field(..., description="Text to embed")
    model: str = Field(
        "nomic-embed-text", description="Embedding model to use"
    )


class EmbeddingResponse(BaseModel):
    """Response with embeddings."""

    embedding: list[float]
    """Vector embedding"""

    model: str
    """Model used"""

    dimensions: int
    """Embedding dimension"""


class ModelPullRequest(BaseModel):
    """Request to download a model."""

    model_name: str = Field(..., description="Model identifier (e.g., 'llama2:latest')")


class ConversationMessage(BaseModel):
    """Message in conversation history."""

    role: str = Field(..., description="Message role: user, assistant, system")
    content: str = Field(..., description="Message content")


class ConversationRequest(BaseModel):
    """Request for conversation with context."""

    model: str = Field(..., description="Model for generation")
    messages: list[ConversationMessage] = Field(..., description="Conversation history")
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    stream: bool = Field(True, description="Stream response")


# Endpoints


@router.get("/models")
async def list_models(
    manager: OllamaModelManager = Depends(get_model_manager),
) -> ListModelsResponse:
    """List all available Ollama models.

    Returns:
        Response with available models and metadata
    """
    try:
        models = await manager.list_available_models()
        return ListModelsResponse(models=models, total=len(models))
    except Exception as e:
        log.error(f"Failed to list models: {e}")
        raise HTTPException(status_code=500, detail="Failed to list models")


@router.get("/models/{model_name}")
async def get_model(
    model_name: str,
    manager: OllamaModelManager = Depends(get_model_manager),
) -> Model:
    """Get details for a specific model.

    Args:
        model_name: Model identifier to retrieve

    Returns:
        Model details and metadata
    """
    try:
        models = await manager.list_available_models()
        for model in models:
            if model.name == model_name:
                return model
        raise HTTPException(status_code=404, detail=f"Model {model_name} not found")
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Failed to get model details: {e}")
        raise HTTPException(status_code=500, detail="Failed to get model details")


@router.post("/generate")
async def generate(
    request: GenerateRequest,
    manager: OllamaModelManager = Depends(get_model_manager),
) -> StreamingResponse | GenerateResponse:
    """Generate text using specified model.

    Supports both streaming and non-streaming responses based on request.

    Args:
        request: Generation request with model and parameters
        manager: Model manager instance

    Returns:
        Text generation response (streaming or complete)
    """
    try:
        ollama_request = OllamaGenerateRequest(
            model=request.model,
            prompt=request.prompt,
            system=request.system,
            temperature=request.temperature,
            top_p=request.top_p,
            top_k=request.top_k,
            repeat_penalty=request.repeat_penalty,
            num_predict=request.num_predict,
            stream=request.stream,
        )

        if request.stream:
            async def generate_stream() -> AsyncGenerator[str, None]:
                """Stream generation responses as Server-Sent Events."""
                async for response in manager.generate(ollama_request):
                    yield f"data: {response.model_dump_json()}\n\n"

            return StreamingResponse(
                generate_stream(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                },
            )
        else:
            # Non-streaming: collect all and return
            full_response = ""
            final_data = None
            async for response in manager.generate(ollama_request):
                full_response += response.response
                if response.done:
                    final_data = response

            return GenerateResponse(
                model=final_data.model if final_data else request.model,
                prompt=request.prompt,
                response=full_response,
                done=True,
                total_duration=final_data.total_duration if final_data else 0,
                prompt_eval_count=final_data.prompt_eval_count if final_data else 0,
                eval_count=final_data.eval_count if final_data else 0,
            )

    except ValueError as e:
        log.warning(f"Invalid request: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log.error(f"Generation failed: {e}")
        raise HTTPException(status_code=500, detail="Generation failed")


@router.post("/embeddings")
async def create_embedding(
    request: EmbeddingRequest,
    manager: OllamaModelManager = Depends(get_model_manager),
) -> EmbeddingResponse:
    """Generate embeddings for input text.

    Args:
        request: Embedding request with text and model
        manager: Model manager instance

    Returns:
        Vector embedding and metadata
    """
    try:
        embedding = await manager.generate_embedding(
            text=request.text, model=request.model
        )
        return EmbeddingResponse(
            embedding=embedding,
            model=request.model,
            dimensions=len(embedding),
        )
    except Exception as e:
        log.error(f"Embedding generation failed: {e}")
        raise HTTPException(status_code=500, detail="Embedding generation failed")


@router.post("/models/pull")
async def pull_model(
    request: ModelPullRequest,
    manager: OllamaModelManager = Depends(get_model_manager),
) -> dict:
    """Download and prepare a model.

    Args:
        request: Pull request with model identifier
        manager: Model manager instance

    Returns:
        Status of pull operation
    """
    try:
        await manager.pull_model(request.model_name)
        return {
            "status": "success",
            "message": f"Model {request.model_name} pulled successfully",
        }
    except Exception as e:
        log.error(f"Model pull failed: {e}")
        raise HTTPException(status_code=500, detail="Model pull failed")


@router.delete("/models/{model_name}")
async def delete_model(
    model_name: str,
    manager: OllamaModelManager = Depends(get_model_manager),
) -> dict:
    """Delete a model from storage.

    Args:
        model_name: Model identifier to delete
        manager: Model manager instance

    Returns:
        Status of delete operation
    """
    try:
        await manager.delete_model(model_name)
        return {
            "status": "success",
            "message": f"Model {model_name} deleted successfully",
        }
    except Exception as e:
        log.error(f"Model delete failed: {e}")
        raise HTTPException(status_code=500, detail="Model delete failed")


@router.post("/chat")
async def chat_completion(
    request: ConversationRequest,
    manager: OllamaModelManager = Depends(get_model_manager),
) -> StreamingResponse:
    """Chat completion with conversation history.

    Supports multi-turn conversations with model context.

    Args:
        request: Chat request with message history
        manager: Model manager instance

    Returns:
        Chat response (streaming)
    """
    try:
        # Build prompt from conversation history
        system_prompt = "You are a helpful assistant."
        conversation_text = ""

        for msg in request.messages:
            if msg.role == "system":
                system_prompt = msg.content
            else:
                conversation_text += f"{msg.role}: {msg.content}\n"

        conversation_text += "assistant: "

        ollama_request = OllamaGenerateRequest(
            model=request.model,
            prompt=conversation_text,
            system=system_prompt,
            temperature=request.temperature,
            stream=request.stream,
        )

        async def chat_stream() -> AsyncGenerator[str, None]:
            """Stream chat responses as Server-Sent Events."""
            async for response in manager.generate(ollama_request):
                yield f"data: {response.model_dump_json()}\n\n"

        return StreamingResponse(
            chat_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )

    except Exception as e:
        log.error(f"Chat completion failed: {e}")
        raise HTTPException(status_code=500, detail="Chat completion failed")
