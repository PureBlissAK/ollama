"""Embeddings endpoints - Semantic search with sentence-transformers"""
from typing import List, Optional
import numpy as np

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from ollama.services import init_vector_db

router = APIRouter()


class EmbeddingsRequest(BaseModel):
    """Embeddings request model"""
    model: str = Field(
        default="all-minilm-l6-v2",
        description="Model name (all-minilm-l6-v2, all-mpnet-base-v2, etc)"
    )
    prompt: str = Field(..., description="Text to embed", min_length=1, max_length=1024)


class EmbeddingsResponse(BaseModel):
    """Embeddings response model"""
    embedding: List[float] = Field(..., description="Vector embedding")
    model: str = Field(..., description="Model used")
    dimensions: int = Field(..., description="Embedding dimensions")


class SemanticSearchRequest(BaseModel):
    """Semantic search request"""
    collection: str = Field(..., description="Qdrant collection name")
    query: str = Field(..., description="Query text")
    model: str = Field(default="all-minilm-l6-v2", description="Embedding model")
    limit: int = Field(default=10, ge=1, le=100)
    score_threshold: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score"
    )


class SearchResult(BaseModel):
    """Search result item"""
    id: str
    score: float
    text: Optional[str] = None


class SemanticSearchResponse(BaseModel):
    """Semantic search response"""
    query: str
    results: List[SearchResult]
    count: int


# Initialize embedding model on module load
try:
    from sentence_transformers import SentenceTransformer
    _embedding_models = {}
    
    def get_embedding_model(model_name: str = "all-minilm-l6-v2"):
        """Get or load embedding model (cached)"""
        if model_name not in _embedding_models:
            _embedding_models[model_name] = SentenceTransformer(model_name)
        return _embedding_models[model_name]
    
except ImportError:
    def get_embedding_model(model_name: str = "all-minilm-l6-v2"):
        raise ImportError(
            "sentence-transformers not installed. "
            "Install with: pip install sentence-transformers"
        )


@router.post("/embeddings", response_model=EmbeddingsResponse)
async def create_embeddings(request: EmbeddingsRequest):
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
            embedding=embedding,
            model=request.model,
            dimensions=len(embedding)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Embedding generation failed: {str(e)}"
        )


@router.post("/semantic-search", response_model=SemanticSearchResponse)
async def semantic_search(
    request: SemanticSearchRequest
):
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
                detail="Vector database not initialized"
            )
        
        # Check if collection exists
        if not await _vector_manager.collection_exists(request.collection):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collection '{request.collection}' not found"
            )
        
        # Generate query embedding
        model = get_embedding_model(request.model)
        query_vector = model.encode(request.query).tolist()
        
        # Search in vector database
        results = await _vector_manager.search_vectors(
            collection_name=request.collection,
            query_vector=query_vector,
            limit=request.limit,
            score_threshold=request.score_threshold
        )
        
        # Format results
        search_results = []
        for result in results:
            search_results.append(
                SearchResult(
                    id=str(result.id),
                    score=float(result.score),
                    text=getattr(result.payload, "text", None)
                )
            )
        
        return SemanticSearchResponse(
            query=request.query,
            results=search_results,
            count=len(search_results)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )

