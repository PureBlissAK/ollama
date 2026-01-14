"""Embeddings endpoints - Semantic search with sentence-transformers"""

from typing import Any

from fastapi import APIRouter, HTTPException, status

from ollama.api.schemas.embeddings_request import EmbeddingsRequest
from ollama.api.schemas.embeddings_response import EmbeddingsResponse
from ollama.api.schemas.search_result import SearchResult
from ollama.api.schemas.semantic_search_request import SemanticSearchRequest
from ollama.api.schemas.semantic_search_response import SemanticSearchResponse

router = APIRouter()

# Initialize embedding model on module load
try:
    from sentence_transformers import SentenceTransformer  # type: ignore[import-untyped]

    _embedding_models: dict[str, Any] = {}

    def get_embedding_model(model_name: str = "all-minilm-l6-v2") -> Any:
        """Get or load embedding model (cached)"""
        if model_name not in _embedding_models:
            _embedding_models[model_name] = SentenceTransformer(model_name)
        return _embedding_models[model_name]

except ImportError:

    def get_embedding_model(model_name: str = "all-minilm-l6-v2") -> Any:
        raise ImportError(
            "sentence-transformers not installed. "
            "Install with: pip install sentence-transformers"
        )


@router.post("/embeddings", response_model=EmbeddingsResponse)
async def create_embeddings(request: EmbeddingsRequest) -> EmbeddingsResponse:
    """
    Generate text embeddings using sentence transformers

    Creates vector representations of text for semantic search and RAG applications.

    **Models:**
    - `all-minilm-l6-v2`: Fast, 384 dimensions (default)
    - `all-mpnet-base-v2`: Accurate, 768 dimensions
    - `all-distilroberta-v1`: Balanced, 768 dimensions

    **Usage:**
    ```json
    {
        "model": "all-minilm-l6-v2",
        "prompt": "What is machine learning?"
    }
    ```
    """
    try:
        model = get_embedding_model(request.model)

        # Generate embedding
        embedding = model.encode(request.prompt).tolist()

        return EmbeddingsResponse(
            embedding=embedding, model=request.model, dimensions=len(embedding)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Embedding generation failed: {e!s}",
        ) from e


@router.post("/semantic-search", response_model=SemanticSearchResponse)
async def semantic_search(request: SemanticSearchRequest) -> SemanticSearchResponse:
    """
    Perform semantic search in Qdrant vector database

    Finds similar vectors based on semantic meaning.

    **Process:**
    1. Embed query text using specified model
    2. Search Qdrant collection for similar vectors
    3. Return results with similarity scores

    **Usage:**
    ```json
    {
        "collection": "documents",
        "query": "How to use embeddings?",
        "model": "all-minilm-l6-v2",
        "limit": 10,
        "score_threshold": 0.7
    }
    ```
    """
    try:
        from ollama.services.vector import _vector_manager

        if _vector_manager is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Vector database not initialized",
            )

        # Check if collection exists
        if not await _vector_manager.collection_exists(request.collection):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collection '{request.collection}' not found",
            )

        # Generate query embedding
        model = get_embedding_model(request.model)
        query_vector = model.encode(request.query).tolist()

        # Search in vector database
        results = await _vector_manager.search_vectors(
            collection_name=request.collection,
            query_vector=query_vector,
            limit=request.limit,
            score_threshold=request.score_threshold,
        )

        # Format results
        search_results = []
        for result in results:
            search_results.append(
                SearchResult(
                    id=str(result.id),
                    score=float(result.score),
                    text=getattr(result.payload, "text", None),
                )
            )

        return SemanticSearchResponse(
            query=request.query, results=search_results, count=len(search_results)
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Search failed: {e!s}"
        ) from e
