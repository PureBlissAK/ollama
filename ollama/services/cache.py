"""
Cache Service - Redis Connection Management
Provides Redis client pooling, caching, and rate limiting
"""

import logging
from typing import Any, Optional, Union
import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


class CacheManager:
    """Manages Redis connection pool and cache operations"""
    
    def __init__(self, redis_url: str, db: int = 0, encoding: str = "utf-8"):
        """
        Initialize cache manager
        
        Args:
            redis_url: Redis connection string (redis://hostname:port)
            db: Redis database number (0-15)
            encoding: String encoding
        """
        self.redis_url = redis_url
        self.db = db
        self.encoding = encoding
        self.pool: Optional[ConnectionPool] = None
        self.client: Optional[redis.Redis] = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize Redis connection pool (called on startup)"""
        try:
            # Create connection pool
            self.pool = ConnectionPool.from_url(
                self.redis_url,
                db=self.db,
                encoding=self.encoding,
                decode_responses=True,
                max_connections=50,
                socket_keepalive=True,
                socket_keepalive_options={
                    1: 3,  # TCP_KEEPIDLE
                    2: 3,  # TCP_KEEPINTVL
                    3: 3,  # TCP_KEEPCNT
                }
            )
            
            # Create async Redis client
            self.client = redis.Redis(connection_pool=self.pool)
            
            # Test connection
            await self.client.ping()
            self._initialized = True
            logger.info("✅ Redis connection established")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            raise
    
    async def close(self):
        """Close Redis connection pool (called on shutdown)"""
        if self.client:
            await self.client.close()
        if self.pool:
            self.pool.disconnect()
        logger.info("✅ Redis connection pool closed")
    
    async def get(self, key: str) -> Optional[str]:
        """Get value from cache"""
        if not self._initialized:
            return None
        try:
            return await self.client.get(key)
        except RedisError as e:
            logger.warning(f"Cache GET error: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache with TTL"""
        if not self._initialized:
            return False
        try:
            await self.client.setex(key, ttl, str(value))
            return True
        except RedisError as e:
            logger.warning(f"Cache SET error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        if not self._initialized:
            return False
        try:
            await self.client.delete(key)
            return True
        except RedisError as e:
            logger.warning(f"Cache DELETE error: {e}")
            return False
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment counter for rate limiting"""
        if not self._initialized:
            return 0
        try:
            return await self.client.incrby(key, amount)
        except RedisError as e:
            logger.warning(f"Cache INCREMENT error: {e}")
            return 0
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        if not self._initialized:
            return False
        try:
            return await self.client.exists(key) > 0
        except RedisError as e:
            logger.warning(f"Cache EXISTS error: {e}")
            return False


# Global cache manager instance
_cache_manager: Optional[CacheManager] = None


def init_cache(redis_url: str, db: int = 0) -> CacheManager:
    """Initialize global cache manager"""
    global _cache_manager
    _cache_manager = CacheManager(redis_url, db=db)
    return _cache_manager


async def get_cache() -> CacheManager:
    """Get cache manager instance"""
    if _cache_manager is None:
        raise RuntimeError("Cache manager not initialized")
    return _cache_manager
