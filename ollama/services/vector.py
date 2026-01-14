"""
Vector Database Service - Qdrant Connection Management
Provides vector database client for semantic search and RAG
"""

import logging
from typing import Any, Optional

from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import Distance, VectorParams

logger = logging.getLogger(__name__)


class VectorManager:
    """Manages Qdrant vector database connection and operations"""

    def __init__(self, qdrant_url: str, api_key: Optional[str] = None):
        """
        Initialize vector manager

        Args:
            qdrant_url: Qdrant server URL (http://hostname:port)
            api_key: Optional API key for Qdrant
        """
        self.qdrant_url = qdrant_url
        self.api_key = api_key
        self.client: Optional[AsyncQdrantClient] = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize Qdrant client (called on startup)"""
        try:
            self.client = AsyncQdrantClient(
                url=self.qdrant_url,
                api_key=self.api_key,
                timeout=30,
            )

            # Test connection
            await self.client.get_collections()
            self._initialized = True
            logger.info("✅ Qdrant connection established")

        except Exception as e:
            logger.error(f"❌ Failed to connect to Qdrant: {e}")
            raise

    async def close(self) -> None:
        """Close Qdrant client (called on shutdown)"""
        if self.client:
            await self.client.close()
        logger.info("✅ Qdrant client closed")

    async def create_collection(
        self, collection_name: str, vector_size: int, distance: Distance = Distance.COSINE, **kwargs
    ) -> bool:
        """Create new vector collection"""
        if not self._initialized:
            logger.warning("Vector manager not initialized")
            return False

        try:
            await self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=vector_size, distance=distance),
                **kwargs,
            )
            logger.info(f"✅ Created collection: {collection_name}")
            return True
        except Exception as e:
            logger.warning(f"Collection creation error: {e}")
            return False

    async def upsert_vectors(self, collection_name: str, points: list[dict[str, Any]]) -> bool:
        """Upsert vectors to collection"""
        if not self._initialized:
            return False

        try:
            await self.client.upsert(collection_name=collection_name, points=points, wait=True)
            return True
        except Exception as e:
            logger.warning(f"Upsert error: {e}")
            return False

    async def search_vectors(
        self,
        collection_name: str,
        query_vector: list[float],
        limit: int = 10,
        score_threshold: Optional[float] = None,
        **kwargs,
    ) -> list[dict[str, Any]]:
        """Search for similar vectors"""
        if not self._initialized:
            return []

        try:
            results = await self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold,
                **kwargs,
            )
            return results
        except Exception as e:
            logger.warning(f"Search error: {e}")
            return []

    async def delete_collection(self, collection_name: str) -> bool:
        """Delete vector collection"""
        if not self._initialized:
            return False

        try:
            await self.client.delete_collection(collection_name)
            logger.info(f"✅ Deleted collection: {collection_name}")
            return True
        except Exception as e:
            logger.warning(f"Delete error: {e}")
            return False

    async def collection_exists(self, collection_name: str) -> bool:
        """Check if collection exists"""
        if not self._initialized:
            return False

        try:
            collections = await self.client.get_collections()
            return any(c.name == collection_name for c in collections.collections)
        except Exception as e:
            logger.warning(f"Collection check error: {e}")
            return False


# Global vector manager instance
_vector_manager: Optional[VectorManager] = None


def init_vector_db(qdrant_url: str, api_key: Optional[str] = None) -> VectorManager:
    """Initialize global vector manager"""
    global _vector_manager
    _vector_manager = VectorManager(qdrant_url, api_key=api_key)
    return _vector_manager


async def get_vector_db() -> VectorManager:
    """Get vector manager instance"""
    if _vector_manager is None:
        raise RuntimeError("Vector manager not initialized")
    return _vector_manager
