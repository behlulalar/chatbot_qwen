"""
Cache Manager for performance optimization.

Implements multi-level caching:
1. Redis for distributed cache (query & response)
2. In-memory LRU for hot data
"""
import json
import hashlib
import redis
from typing import Optional, Any, Dict, List, cast
from cachetools import LRUCache
from datetime import timedelta
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Multi-level cache manager.
    
    Level 1: In-memory LRU (fast, limited size)
    Level 2: Redis (distributed, persistent)
    """
    
    def __init__(
        self,
        redis_host: str = "localhost",
        redis_port: int = 6379,
        redis_db: int = 0,
        redis_enabled: bool = True,
        lru_maxsize: int = 100
    ):
        """
        Initialize cache manager.
        
        Args:
            redis_host: Redis server host
            redis_port: Redis server port
            redis_db: Redis database number
            redis_enabled: Enable Redis cache
            lru_maxsize: Max size for in-memory LRU cache
        """
        self.redis_enabled = redis_enabled
        
        # In-memory LRU cache (Level 1 - fastest)
        self.lru_cache = LRUCache(maxsize=lru_maxsize)
        
        # Redis cache (Level 2 - distributed)
        if self.redis_enabled:
            try:
                self.redis_client = redis.Redis(
                    host=redis_host,
                    port=redis_port,
                    db=redis_db,
                    decode_responses=True,
                    socket_connect_timeout=2
                )
                # Test connection
                self.redis_client.ping()
                logger.info(f"Redis cache connected: {redis_host}:{redis_port}")
            except (redis.ConnectionError, redis.TimeoutError) as e:
                logger.warning(f"Redis connection failed: {e}. Falling back to in-memory only.")
                self.redis_enabled = False
                self.redis_client = None
        else:
            self.redis_client = None
            logger.info("Redis cache disabled. Using in-memory only.")
    
    def _generate_key(self, prefix: str, data: Any) -> str:
        """
        Generate cache key from data.
        
        Args:
            prefix: Key prefix (e.g., 'query', 'response')
            data: Data to hash
        
        Returns:
            Cache key
        """
        if isinstance(data, str):
            hash_str = data
        elif isinstance(data, dict):
            hash_str = json.dumps(data, sort_keys=True)
        else:
            hash_str = str(data)
        
        hash_digest = hashlib.md5(hash_str.encode()).hexdigest()
        return f"{prefix}:{hash_digest}"
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache (tries LRU first, then Redis).
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None
        """
        # Level 1: In-memory LRU (fastest)
        if key in self.lru_cache:
            logger.debug(f"Cache HIT (LRU): {key}")
            return self.lru_cache[key]
        
        # Level 2: Redis (distributed)
        if self.redis_enabled and self.redis_client:
            try:
                value = self.redis_client.get(key)
                if value:
                    logger.debug(f"Cache HIT (Redis): {key}")
                    # Promote to LRU (redis returns str when decode_responses=True)
                    parsed_value = json.loads(cast(str, value))
                    self.lru_cache[key] = parsed_value
                    return parsed_value
            except Exception as e:
                logger.error(f"Redis GET error: {e}")
        
        logger.debug(f"Cache MISS: {key}")
        return None
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in cache (both LRU and Redis).
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (Redis only)
        
        Returns:
            Success status
        """
        # Level 1: In-memory LRU
        self.lru_cache[key] = value
        
        # Level 2: Redis
        if self.redis_enabled and self.redis_client:
            try:
                json_value = json.dumps(value)
                if ttl:
                    self.redis_client.setex(key, ttl, json_value)
                else:
                    self.redis_client.set(key, json_value)
                logger.debug(f"Cache SET: {key} (TTL: {ttl}s)")
                return True
            except Exception as e:
                logger.error(f"Redis SET error: {e}")
                return False
        
        return True
    
    def delete(self, key: str) -> bool:
        """
        Delete key from cache.
        
        Args:
            key: Cache key
        
        Returns:
            Success status
        """
        # Level 1: LRU
        self.lru_cache.pop(key, None)
        
        # Level 2: Redis
        if self.redis_enabled and self.redis_client:
            try:
                self.redis_client.delete(key)
                logger.debug(f"Cache DELETE: {key}")
                return True
            except Exception as e:
                logger.error(f"Redis DELETE error: {e}")
                return False
        
        return True
    
    def clear(self, pattern: Optional[str] = None) -> int:
        """
        Clear cache (optionally by pattern).
        
        Args:
            pattern: Key pattern to match (e.g., 'query:*')
        
        Returns:
            Number of keys deleted
        """
        count = 0
        
        # Level 1: LRU
        if pattern:
            # Clear matching keys
            keys_to_delete = [k for k in self.lru_cache.keys() if pattern.replace('*', '') in k]
            for key in keys_to_delete:
                self.lru_cache.pop(key, None)
                count += 1
        else:
            # Clear all
            count = len(self.lru_cache)
            self.lru_cache.clear()
        
        # Level 2: Redis
        if self.redis_enabled and self.redis_client:
            try:
                if pattern:
                    keys = cast(List[str], self.redis_client.keys(pattern))
                    if keys:
                        count += cast(int, self.redis_client.delete(*keys))
                else:
                    self.redis_client.flushdb()
                
                logger.info(f"Cache CLEARED: {count} keys (pattern: {pattern})")
            except Exception as e:
                logger.error(f"Redis CLEAR error: {e}")
        
        return count
    
    def get_stats(self) -> Dict:
        """
        Get cache statistics.
        
        Returns:
            Cache stats dictionary
        """
        stats = {
            "lru_size": len(self.lru_cache),
            "lru_maxsize": self.lru_cache.maxsize,
            "redis_enabled": self.redis_enabled
        }
        
        if self.redis_enabled and self.redis_client:
            try:
                info = cast(Dict[str, Any], self.redis_client.info('stats'))
                stats.update({
                    "redis_hits": info.get('keyspace_hits', 0),
                    "redis_misses": info.get('keyspace_misses', 0),
                    "redis_keys": cast(int, self.redis_client.dbsize())
                })
            except Exception as e:
                logger.error(f"Redis STATS error: {e}")
        
        return stats


# Singleton instance
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """Get or create cache manager singleton."""
    global _cache_manager
    
    if _cache_manager is None:
        _cache_manager = CacheManager(
            redis_host=settings.redis_host,
            redis_port=settings.redis_port,
            redis_enabled=settings.redis_enabled,
            lru_maxsize=100
        )
    
    return _cache_manager
