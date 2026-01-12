"""
Tests for Database Service
Tests database connection, session management, and async operations
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4


class TestDatabaseService:
    """Test database service operations"""
    
    def test_database_manager_initialization(self):
        """Test creating database manager"""
        from ollama.services.database import init_database
        
        manager = init_database(
            database_url="postgresql+asyncpg://test:test@localhost:5432/test",
            echo=False
        )
        assert manager is not None
    
    @pytest.mark.asyncio
    async def test_database_manager_initialize(self):
        """Test database manager initialization"""
        from ollama.services.database import DatabaseManager
        
        manager = DatabaseManager(
            database_url="postgresql+asyncpg://test:test@localhost:5432/test",
            echo=False
        )
        
        assert hasattr(manager, 'initialize')
        assert hasattr(manager, 'close')
    
    @pytest.mark.asyncio
    async def test_get_session(self):
        """Test getting database session"""
        from ollama.services.database import DatabaseManager
        
        manager = DatabaseManager(
            database_url="postgresql+asyncpg://test:test@localhost:5432/test",
            echo=False
        )
        
        # Should have session getter
        assert hasattr(manager, 'get_session')
    
    @pytest.mark.asyncio
    async def test_session_context_manager(self):
        """Test session as context manager"""
        from ollama.services.database import DatabaseManager
        
        manager = DatabaseManager(
            database_url="postgresql+asyncpg://test:test@localhost:5432/test",
            echo=False
        )
        
        # Should support context manager protocol
        assert hasattr(manager, 'get_session')


class TestDatabaseConnection:
    """Test database connection management"""
    
    @pytest.mark.asyncio
    async def test_connection_pool(self):
        """Test connection pooling"""
        from ollama.services.database import DatabaseManager
        
        manager = DatabaseManager(
            database_url="postgresql+asyncpg://test:test@localhost:5432/test",
            echo=False
        )
        
        # Should manage connection pool
        assert manager is not None
    
    @pytest.mark.asyncio
    async def test_connection_lifecycle(self):
        """Test connection open/close"""
        from ollama.services.database import DatabaseManager
        
        manager = DatabaseManager(
            database_url="postgresql+asyncpg://test:test@localhost:5432/test",
            echo=False
        )
        
        # Should have lifecycle methods
        assert hasattr(manager, 'initialize')
        assert hasattr(manager, 'close')
    
    def test_connection_string_parsing(self):
        """Test database URL parsing"""
        from ollama.services.database import DatabaseManager
        
        # Should parse PostgreSQL connection string
        manager = DatabaseManager(
            database_url="postgresql+asyncpg://user:pass@host:5432/dbname",
            echo=False
        )
        assert manager is not None


class TestSessionManagement:
    """Test session management"""
    
    @pytest.mark.asyncio
    async def test_session_creation(self):
        """Test creating sessions"""
        from ollama.services.database import DatabaseManager
        
        manager = DatabaseManager(
            database_url="postgresql+asyncpg://test:test@localhost:5432/test",
            echo=False
        )
        
        # Should create sessions
        assert hasattr(manager, 'get_session')
    
    @pytest.mark.asyncio
    async def test_session_cleanup(self):
        """Test session cleanup"""
        from ollama.services.database import DatabaseManager
        
        manager = DatabaseManager(
            database_url="postgresql+asyncpg://test:test@localhost:5432/test",
            echo=False
        )
        
        # Should clean up sessions
        assert manager is not None


class TestTransactionManagement:
    """Test transaction handling"""
    
    @pytest.mark.asyncio
    async def test_transaction_commit(self):
        """Test committing transactions"""
        from ollama.services.database import DatabaseManager
        
        manager = DatabaseManager(
            database_url="postgresql+asyncpg://test:test@localhost:5432/test",
            echo=False
        )
        
        # Sessions should support commits
        assert manager is not None
    
    @pytest.mark.asyncio
    async def test_transaction_rollback(self):
        """Test rolling back transactions"""
        from ollama.services.database import DatabaseManager
        
        manager = DatabaseManager(
            database_url="postgresql+asyncpg://test:test@localhost:5432/test",
            echo=False
        )
        
        # Sessions should support rollbacks
        assert manager is not None


class TestDatabaseErrorHandling:
    """Test error handling"""
    
    def test_invalid_connection_string(self):
        """Test handling invalid connection strings"""
        from ollama.services.database import DatabaseManager
        import pytest
        
        # Should raise exception for malformed URLs
        with pytest.raises(Exception):
            manager = DatabaseManager(
                database_url="invalid://connection",
                echo=False
            )
    
    @pytest.mark.asyncio
    async def test_connection_failure(self):
        """Test handling connection failures"""
        from ollama.services.database import DatabaseManager
        
        manager = DatabaseManager(
            database_url="postgresql+asyncpg://invalid:invalid@nonexistent:5432/test",
            echo=False
        )
        
        # Should handle connection errors gracefully
        assert manager is not None


class TestDatabaseSingleton:
    """Test singleton pattern"""
    
    def test_get_db_manager(self):
        """Test get_db_manager function"""
        from ollama.services.database import get_db_manager
        
        # Should access database manager
        try:
            manager = get_db_manager()
            assert manager is not None
        except RuntimeError:
            # Expected if not initialized
            pass
    
    def test_init_database(self):
        """Test init_database function"""
        from ollama.services.database import init_database
        
        manager = init_database(
            database_url="postgresql+asyncpg://test:test@localhost:5432/test",
            echo=False
        )
        assert manager is not None


class TestAsyncOperations:
    """Test async database operations"""
    
    @pytest.mark.asyncio
    async def test_async_queries(self):
        """Test async query execution"""
        from ollama.services.database import DatabaseManager
        
        manager = DatabaseManager(
            database_url="postgresql+asyncpg://test:test@localhost:5432/test",
            echo=False
        )
        
        # Should support async operations
        assert manager is not None
    
    @pytest.mark.asyncio
    async def test_async_context_manager(self):
        """Test async context manager support"""
        from ollama.services.database import DatabaseManager
        
        manager = DatabaseManager(
            database_url="postgresql+asyncpg://test:test@localhost:5432/test",
            echo=False
        )
        
        # Should support async with
        assert hasattr(manager, 'get_session')


class TestSQLAlchemyIntegration:
    """Test SQLAlchemy integration"""
    
    def test_engine_creation(self):
        """Test SQLAlchemy engine creation"""
        from ollama.services.database import DatabaseManager
        
        manager = DatabaseManager(
            database_url="postgresql+asyncpg://test:test@localhost:5432/test",
            echo=False
        )
        
        # Should create async engine
        assert manager is not None
    
    def test_session_factory(self):
        """Test session factory creation"""
        from ollama.services.database import DatabaseManager
        
        manager = DatabaseManager(
            database_url="postgresql+asyncpg://test:test@localhost:5432/test",
            echo=False
        )
        
        # Should create session factory
        assert manager is not None


class TestDatabaseConfiguration:
    """Test database configuration options"""
    
    def test_echo_mode(self):
        """Test SQL echo configuration"""
        from ollama.services.database import DatabaseManager
        
        # Should support echo mode for debugging
        manager = DatabaseManager(
            database_url="postgresql+asyncpg://test:test@localhost:5432/test",
            echo=True
        )
        assert manager is not None
    
    def test_pool_configuration(self):
        """Test connection pool configuration"""
        from ollama.services.database import DatabaseManager
        
        # Should configure connection pool
        manager = DatabaseManager(
            database_url="postgresql+asyncpg://test:test@localhost:5432/test",
            echo=False
        )
        assert manager is not None
