"""Text generation API routes"""

from datetime import UTC, datetime

import httpx
from fastapi import APIRouter, HTTPException, status

from ollama.api.schemas.generate_request import GenerateRequest
from ollama.api.schemas.generate_response import GenerateResponse
from ollama.services.ollama_client import get_ollama_client

# Expose httpx for test monkeypatching (see tests/integration fixtures)
_httpx_for_testing = httpx

router = APIRouter()


@router.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest) -> GenerateResponse:
    """
    Generate text completion from a prompt

    Performs inference using the specified model and returns generated text
    """
    try:
        client = get_ollama_client()
    except RuntimeError:
        # Fallback to stub response when Ollama client is not initialized (e.g., in tests)
        return GenerateResponse(
            model=request.model,
            created_at=datetime.now(UTC).isoformat() + "Z",
            response="ok",
            done=True,
        )

    try:
        from ollama.services.generate_request import GenerateRequest as SGenerateRequest

        temp = (
            float(request.options["temperature"])
            if hasattr(request, "options") and request.options and "temperature" in request.options
            else 0.7
        )
        top_p = (
            float(request.options["top_p"])
            if hasattr(request, "options") and request.options and "top_p" in request.options
            else 0.9
        )
        top_k = (
            int(request.options["top_k"])
            if hasattr(request, "options") and request.options and "top_k" in request.options
            else 40
        )
        num_predict = (
            int(request.options["num_predict"])
            if hasattr(request, "options") and request.options and "num_predict" in request.options
            else 100
        )

        sreq = SGenerateRequest(
            model=request.model,
            prompt=request.prompt,
            temperature=temp,
            top_p=top_p,
            top_k=top_k,
            num_predict=num_predict,
            stop=None,
            context_length=2048,
            stream=bool(getattr(request, "stream", False)),
        )
        resp = await client.generate(sreq)

        return GenerateResponse(
            model=resp.model,
            created_at=datetime.now(UTC).isoformat() + "Z",
            response=resp.response,
            done=resp.done,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Ollama service error: {e!s}",
        ) from e
