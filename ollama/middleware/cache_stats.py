"""Track cache performance statistics."""

import logging

from ollama.services import CacheManager

logger = logging.getLogger(__name__)


class CacheStats:
    """Track cache performance statistics."""

    def __init__(self, cache_manager: CacheManager):
        self.cache_manager = cache_manager

    async def record_hit(self, key: str) -> None:
        """Record cache hit."""
        stats_key = f"stats:hits:{key}"
        await self.cache_manager.increment(stats_key, 1)
        await self.cache_manager.client.expire(stats_key, 86400)  # 24h

    async def record_miss(self, key: str) -> None:
        """Record cache miss."""
        stats_key = f"stats:misses:{key}"
        await self.cache_manager.increment(stats_key, 1)
        await self.cache_manager.client.expire(stats_key, 86400)  # 24h

    async def get_stats(self, key: str) -> dict:
        """Get cache statistics for a key."""
        hits_key = f"stats:hits:{key}"
        misses_key = f"stats:misses:{key}"

        hits = await self.cache_manager.client.get(hits_key)
        misses = await self.cache_manager.client.get(misses_key)

        hits = int(hits) if hits else 0
        misses = int(misses) if misses else 0
        total = hits + misses

        hit_rate = (hits / total * 100) if total > 0 else 0

        return {
            "hits": hits,
            "misses": misses,
            "total": total,
            "hit_rate": f"{hit_rate:.2f}%",
        }
