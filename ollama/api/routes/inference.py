"""Ollama inference API routes.

Provides endpoints for text generation, embeddings, model management,
and conversation history with streaming support.
"""

import logging
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from starlette.responses import StreamingResponse

from ollama.api.dependencies import get_model_manager
from ollama.api.schemas.inference_conversation_request import ConversationRequest
from ollama.api.schemas.inference_embedding_request import EmbeddingRequest
from ollama.api.schemas.inference_embedding_response import EmbeddingResponse
from ollama.api.schemas.inference_generate_request import GenerateRequest
from ollama.api.schemas.inference_generate_response import GenerateResponse
from ollama.api.schemas.inference_list_models_response import ListModelsResponse
from ollama.api.schemas.inference_model_pull_request import ModelPullRequest
from ollama.services.models import (
    GenerateRequest as OllamaGenerateRequest,
)
from ollama.services.models import (
    Model,
    OllamaModelManager,
)

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["inference"])


# Request/Response Schemas moved to ollama.api.schemas.*


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
        embedding = await manager.generate_embedding(text=request.text, model=request.model)
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
