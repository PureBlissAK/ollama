"""
Ollama Services - Infrastructure and Data Layer
Provides connection pooling and lifecycle management for external services
"""

from .database import DatabaseManager, get_db, init_database, get_db_manager
from .cache import CacheManager, init_cache
from .vector import VectorManager, init_vector_db

__all__ = [
    "DatabaseManager",
    "CacheManager",
    "VectorManager",
    "init_database",
    "init_cache",
    "init_vector_db",
    "get_db",
    "get_db_manager",
]
