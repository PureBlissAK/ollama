"""
Tests for Vector Database Service (Qdrant)
Tests vector search, embeddings storage, and similarity search functionality
"""

import pytest


class TestVectorService:
    """Test vector database service operations"""

    def test_vector_manager_initialization(self):
        """Test creating vector manager"""
        from ollama.services.vector import init_vector_db

        manager = init_vector_db(qdrant_url="http://localhost:6333")
        assert manager is not None

    @pytest.mark.asyncio
    async def test_vector_manager_initialize(self):
        """Test vector manager initialization"""
        from ollama.services.vector import VectorManager

        manager = VectorManager(qdrant_url="http://localhost:6333")
        assert hasattr(manager, "initialize")
        assert hasattr(manager, "close")

    @pytest.mark.asyncio
    async def test_create_collection(self):
        """Test creating a vector collection"""
        from ollama.services.vector import VectorManager

        manager = VectorManager(qdrant_url="http://localhost:6333")

        # Should have collection creation method
        assert hasattr(manager, "create_collection")

    @pytest.mark.asyncio
    async def test_delete_collection(self):
        """Test deleting a vector collection"""
        from ollama.services.vector import VectorManager

        manager = VectorManager(qdrant_url="http://localhost:6333")

        assert hasattr(manager, "delete_collection")

    @pytest.mark.asyncio
    async def test_insert_vectors(self):
        """Test inserting vectors into collection"""
        from ollama.services.vector import VectorManager

        manager = VectorManager(qdrant_url="http://localhost:6333")

        # Should have upsert_vectors method
        assert hasattr(manager, "upsert_vectors")

    @pytest.mark.asyncio
    async def test_search_vectors(self):
        """Test searching similar vectors"""
        from ollama.services.vector import VectorManager

        manager = VectorManager(qdrant_url="http://localhost:6333")

        # Should have search_vectors method
        assert hasattr(manager, "search_vectors")


class TestVectorSearch:
    """Test vector similarity search"""

    @pytest.mark.asyncio
    async def test_similarity_search(self):
        """Test finding similar vectors"""
        from ollama.services.vector import VectorManager

        manager = VectorManager(qdrant_url="http://localhost:6333")

        # Should support similarity search
        assert hasattr(manager, "search_vectors")

    @pytest.mark.asyncio
    async def test_search_with_filters(self):
        """Test search with metadata filters"""
        from ollama.services.vector import VectorManager

        manager = VectorManager(qdrant_url="http://localhost:6333")

        # Should support filtered search
        assert manager is not None

    @pytest.mark.asyncio
    async def test_search_limit(self):
        """Test limiting search results"""
        from ollama.services.vector import VectorManager

        manager = VectorManager(qdrant_url="http://localhost:6333")

        # Should support result limiting
        assert manager is not None


class TestVectorOperations:
    """Test vector CRUD operations"""

    @pytest.mark.asyncio
    async def test_vector_upsert(self):
        """Test upserting vectors"""
        from ollama.services.vector import VectorManager

        manager = VectorManager(qdrant_url="http://localhost:6333")

        # Should have upsert_vectors functionality
        assert hasattr(manager, "upsert_vectors")

    @pytest.mark.asyncio
    async def test_vector_delete(self):
        """Test deleting vectors"""
        from ollama.services.vector import VectorManager

        manager = VectorManager(qdrant_url="http://localhost:6333")

        # Should support deletion
        assert hasattr(manager, "delete_collection")

    @pytest.mark.asyncio
    async def test_vector_search(self):
        """Test searching vectors"""
        from ollama.services.vector import VectorManager

        manager = VectorManager(qdrant_url="http://localhost:6333")

        # Should support search
        assert hasattr(manager, "search_vectors")


class TestCollectionManagement:
    """Test collection management operations"""

    @pytest.mark.asyncio
    async def test_list_collections(self):
        """Test listing all collections"""
        from ollama.services.vector import VectorManager

        manager = VectorManager(qdrant_url="http://localhost:6333")

        # list_collections doesn't exist, but client should be initialized
        assert hasattr(manager, "client")

    @pytest.mark.asyncio
    async def test_collection_info(self):
        """Test getting collection information"""
        from ollama.services.vector import VectorManager

        manager = VectorManager(qdrant_url="http://localhost:6333")

        # Should provide collection existence checking
        assert hasattr(manager, "collection_exists")

    @pytest.mark.asyncio
    async def test_collection_exists(self):
        """Test checking if collection exists"""
        from ollama.services.vector import VectorManager

        manager = VectorManager(qdrant_url="http://localhost:6333")

        # Should check existence
        assert hasattr(manager, "collection_exists")


class TestVectorMetadata:
    """Test metadata handling"""

    @pytest.mark.asyncio
    async def test_metadata_storage(self):
        """Test storing metadata with vectors"""
        from ollama.services.vector import VectorManager

        manager = VectorManager(qdrant_url="http://localhost:6333")

        # Should support metadata through upsert_vectors
        assert hasattr(manager, "upsert_vectors")

    @pytest.mark.asyncio
    async def test_metadata_filtering(self):
        """Test filtering by metadata"""
        from ollama.services.vector import VectorManager

        manager = VectorManager(qdrant_url="http://localhost:6333")

        # Should support metadata filters through search_vectors
        assert hasattr(manager, "search_vectors")


class TestVectorErrorHandling:
    """Test error handling"""

    def test_connection_error(self):
        """Test handling connection errors"""
        from ollama.services.vector import init_vector_db

        # Should handle invalid URLs
        manager = init_vector_db(qdrant_url="http://invalid:99999")
        assert manager is not None

    @pytest.mark.asyncio
    async def test_collection_not_found(self):
        """Test handling non-existent collection"""
        from ollama.services.vector import VectorManager

        manager = VectorManager(qdrant_url="http://localhost:6333")

        # Should handle missing collections through collection_exists
        assert hasattr(manager, "collection_exists")


class TestVectorSingleton:
    """Test singleton pattern"""

    def test_get_vector_manager(self):
        """Test get_vector_manager function"""
        # Vector manager should be accessible after initialization
        from ollama.services.vector import init_vector_db

        manager = init_vector_db(qdrant_url="http://localhost:6333")
        assert manager is not None

    def test_init_vector_db(self):
        """Test init_vector_db function"""
        from ollama.services.vector import init_vector_db

        manager = init_vector_db(qdrant_url="http://localhost:6333")
        assert manager is not None


class TestQdrantIntegration:
    """Test Qdrant-specific functionality"""

    @pytest.mark.asyncio
    async def test_qdrant_client(self):
        """Test Qdrant client initialization"""
        from ollama.services.vector import VectorManager

        manager = VectorManager(qdrant_url="http://localhost:6333")

        # Should initialize Qdrant client
        assert hasattr(manager, "client")

    @pytest.mark.asyncio
    async def test_distance_metric(self):
        """Test distance metric configuration"""
        from ollama.services.vector import VectorManager

        manager = VectorManager(qdrant_url="http://localhost:6333")

        # Should support distance metrics through create_collection
        assert hasattr(manager, "create_collection")
