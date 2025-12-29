#!/usr/bin/env python3
"""
Redis Cache Middleware - Persistent caching layer for Mordzix AI
Provides: connection pooling, TTL management, cache invalidation, stats tracking
"""

import redis
import json
import hashlib
import logging
from typing import Any, Optional, Union
from datetime import datetime, timedelta
from functools import wraps
import os

logger = logging.getLogger(__name__)

class RedisCache:
    """
    Redis cache manager with connection pooling and automatic serialization
    """
    
    def __init__(
        self,
        host: str = None,
        port: int = None,
        db: int = 0,
        password: str = None,
        max_connections: int = 50,
        decode_responses: bool = True
    ):
        """Initialize Redis connection pool"""
        self.host = host or os.getenv("REDIS_HOST", "localhost")
        self.port = port or int(os.getenv("REDIS_PORT", "6379"))
        self.password = password or os.getenv("REDIS_PASSWORD")
        
        pool_kwargs = {
            "host": self.host,
            "port": self.port,
            "db": db,
            "max_connections": max_connections,
            "decode_responses": decode_responses
        }
        
        if self.password:
            pool_kwargs["password"] = self.password
        
        self.pool = redis.ConnectionPool(**pool_kwargs)
        self.client = redis.Redis(connection_pool=self.pool)
        
        # Test connection
        try:
            self.client.ping()
            logger.info(f"[OK] Redis connected: {self.host}:{self.port}")
        except redis.ConnectionError as e:
            logger.error(f"[FAIL] Redis connection error: {e}")
            raise
    
    def _serialize(self, value: Any) -> str:
        """Serialize Python object to JSON string"""
        if isinstance(value, (str, int, float, bool)):
            return json.dumps({"_v": value, "_t": type(value).__name__})
        return json.dumps(value)
    
    def _deserialize(self, value: str) -> Any:
        """Deserialize JSON string to Python object"""
        try:
            data = json.loads(value)
            if isinstance(data, dict) and "_v" in data and "_t" in data:
                return data["_v"]
            return data
        except (json.JSONDecodeError, TypeError):
            return value
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        Returns None if key doesn't exist
        """
        try:
            value = self.client.get(key)
            if value is None:
                return None
            return self._deserialize(value)
        except Exception as e:
            logger.error(f"Redis GET error for key '{key}': {e}")
            return None
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        nx: bool = False,
        xx: bool = False
    ) -> bool:
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to store (any JSON-serializable object)
            ttl: Time-to-live in seconds (None = no expiration)
            nx: Only set if key doesn't exist
            xx: Only set if key exists
        
        Returns:
            True if successful, False otherwise
        """
        try:
            serialized = self._serialize(value)
            kwargs = {}
            if ttl:
                kwargs["ex"] = ttl
            if nx:
                kwargs["nx"] = True
            if xx:
                kwargs["xx"] = True
            
            result = self.client.set(key, serialized, **kwargs)
            return bool(result)
        except Exception as e:
            logger.error(f"Redis SET error for key '{key}': {e}")
            return False
    
    def setex(self, key: str, ttl: int, value: Any) -> bool:
        """
        Set value with expiration time (Redis compatibility method)
        
        Args:
            key: Cache key
            ttl: Time-to-live in seconds
            value: Value to store
        
        Returns:
            True if successful, False otherwise
        """
        return self.set(key, value, ttl=ttl)
    
    def delete(self, *keys: str) -> int:
        """
        Delete one or more keys
        Returns number of keys deleted
        """
        try:
            return self.client.delete(*keys)
        except Exception as e:
            logger.error(f"Redis DELETE error: {e}")
            return 0
    
    def exists(self, *keys: str) -> int:
        """Check if one or more keys exist"""
        try:
            return self.client.exists(*keys)
        except Exception as e:
            logger.error(f"Redis EXISTS error: {e}")
            return 0
    
    def ttl(self, key: str) -> int:
        """
        Get TTL for key in seconds
        Returns -1 if key exists but has no expiration
        Returns -2 if key doesn't exist
        """
        try:
            return self.client.ttl(key)
        except Exception as e:
            logger.error(f"Redis TTL error for key '{key}': {e}")
            return -2
    
    def expire(self, key: str, seconds: int) -> bool:
        """Set expiration time for key"""
        try:
            return bool(self.client.expire(key, seconds))
        except Exception as e:
            logger.error(f"Redis EXPIRE error for key '{key}': {e}")
            return False
    
    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment value by amount"""
        try:
            return self.client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Redis INCR error for key '{key}': {e}")
            return None
    
    def decrement(self, key: str, amount: int = 1) -> Optional[int]:
        """Decrement value by amount"""
        try:
            return self.client.decrby(key, amount)
        except Exception as e:
            logger.error(f"Redis DECR error for key '{key}': {e}")
            return None
    
    def keys(self, pattern: str = "*") -> list:
        """Get all keys matching pattern"""
        try:
            return [k.decode() if isinstance(k, bytes) else k 
                    for k in self.client.keys(pattern)]
        except Exception as e:
            logger.error(f"Redis KEYS error for pattern '{pattern}': {e}")
            return []
    
    def flush_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        keys = self.keys(pattern)
        if keys:
            return self.delete(*keys)
        return 0
    
    def flush_all(self) -> bool:
        """Flush entire Redis database (use with caution!)"""
        try:
            return bool(self.client.flushdb())
        except Exception as e:
            logger.error(f"Redis FLUSHDB error: {e}")
            return False
    
    def get_stats(self) -> dict:
        """Get Redis server stats"""
        try:
            info = self.client.info()
            return {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory_human", "N/A"),
                "used_memory_peak": info.get("used_memory_peak_human", "N/A"),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "instantaneous_ops_per_sec": info.get("instantaneous_ops_per_sec", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(info),
                "uptime_in_seconds": info.get("uptime_in_seconds", 0)
            }
        except Exception as e:
            logger.error(f"Redis INFO error: {e}")
            return {}
    
    def _calculate_hit_rate(self, info: dict) -> float:
        """Calculate cache hit rate percentage"""
        hits = info.get("keyspace_hits", 0)
        misses = info.get("keyspace_misses", 0)
        total = hits + misses
        if total == 0:
            return 0.0
        return round((hits / total) * 100, 2)
    
    def hash_key(self, *args, **kwargs) -> str:
        """
        Generate cache key from arguments
        Useful for function result caching
        """
        key_data = {
            "args": args,
            "kwargs": sorted(kwargs.items())
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_string.encode()).hexdigest()


# Global Redis instance
_redis_cache: Optional[RedisCache] = None


def get_redis() -> RedisCache:
    """Get or create global Redis cache instance"""
    global _redis_cache
    if _redis_cache is None:
        try:
            _redis_cache = RedisCache()
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
            # Return mock object that does nothing
            class MockRedis:
                def get(self, *args, **kwargs): return None
                def set(self, *args, **kwargs): return False
                def setex(self, *args, **kwargs): return False
                def delete(self, *args, **kwargs): return 0
                def exists(self, *args, **kwargs): return 0
                def get_stats(self): return {}
                def hash_key(self, *args, **kwargs): return ""
            _redis_cache = MockRedis()
    return _redis_cache


def cached(
    ttl: int = 3600,
    key_prefix: str = "",
    include_args: bool = True,
    include_kwargs: bool = True
):
    """
    Decorator for caching function results in Redis
    
    Args:
        ttl: Time-to-live in seconds (default: 1 hour)
        key_prefix: Prefix for cache key (default: function name)
        include_args: Include positional args in cache key
        include_kwargs: Include keyword args in cache key
    
    Example:
        @cached(ttl=300, key_prefix="llm")
        def expensive_llm_call(prompt: str, model: str):
            return call_llm_api(prompt, model)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            redis = get_redis()
            
            # Build cache key
            prefix = key_prefix or f"cache:{func.__module__}.{func.__name__}"
            
            key_parts = [prefix]
            if include_args:
                key_parts.extend(str(arg) for arg in args)
            if include_kwargs:
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            
            cache_key = redis.hash_key(*key_parts)
            
            # Try to get from cache
            cached_result = redis.get(cache_key)
            if cached_result is not None:
                logger.debug(f"[CACHE HIT] {func.__name__}")
                return cached_result
            
            # Execute function
            logger.debug(f"[CACHE MISS] {func.__name__}")
            result = func(*args, **kwargs)
            
            # Store in cache
            redis.set(cache_key, result, ttl=ttl)
            
            return result
        return wrapper
    return decorator


__all__ = [
    "RedisCache",
    "get_redis",
    "cached"
]
