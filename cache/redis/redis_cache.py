import json
import pickle
import logging
from typing import Optional, Any, List, Dict, Union
import redis.asyncio as aioredis
from asyncio import Lock

from ..base_cache import BaseCache, CacheError
from config.redis_config import get_async_redis_connection, redis_config

logger = logging.getLogger(__name__)

class RedisCache(BaseCache):
    """
    Redis implementation of BaseCache interface

    This class implements all 6 abstract methods using real redis operations
    """

    def __init__(self):
        self._redis_client: Optional[aioredis.Redis] = None
        self._lock = Lock() 
    
    async def _get_client(self) -> Optional[aioredis.Redis]:
        """
        getting redis client with lazy initialization
        """
        if self._redis_client is None:
            async with self._lock:
                if self._redis_client is None:
                    self._redis_client = await get_async_redis_connection()
        
        return self._redis_client

    def _serialize_value(self, value: Any) -> str:
        """
        converting python object to string for redis storage
        """
        try:
            return json.dumps(value, default=str)
        except (TypeError, ValueError):
            # fallback to pickle for complex objects (lists, objects, etc..)
            return pickle.dumps(value).decode('latin-1')
        
    def _deserialize_value(self, value: str) -> Any:
        """
        converting redis string back to python object
        """
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            # fallback to pickle for complex objects (lists, objects, etc..)
            try:
                return pickle.loads(value.encode('latin-1'))
            except:
                # if all else fails, return raw string
                return value
        
    # ========================================
    # CORE METHODS (MUST IMPLEMENT)
    # ========================================

    async def get(self, key: str) -> Optional[Any]:
        """
        get value by key from redis
        """
        try:
            client = await self._get_client()
            if not client:
                logger.error("Redis client not initialized")
                return None

            raw_value = await client.get(key)
            if raw_value is None:
                logger.debug(f"Cache miss for key: {key}")
                return None

            # deserialize and return 
            value = self._deserialize_value(raw_value)
            logger.debug(f"Cache hit for key: {key}")
            return value
        
        except Exception as e:
            logger.error(f"Redis get error for key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        set key-value pair in redis with optional ttl
        """
        try:
            client = await self._get_client()
            if not client:
                logger.error("Redis client not initialized")
                return False
            
            serialized_value = self._serialize_value(value)
            if ttl:
                await client.setex(key, ttl, serialized_value)
            else:
                await client.set(key, serialized_value)
            
            logger.debug(f"Cache set for key: {key} with ttl: {ttl}")
            return True
        
        except Exception as e:
            logger.error(f"Redis set error for key {key}: {e}")
            return False
        
    async def delete(self, key: str) -> bool:
        """
        delete key from redis
        """
        try:
            client = await self._get_client()
            if not client:
                logger.error("Redis client not initialized")
                return False
            
            result = await client.delete(key)

            if result > 0:
                logger.debug(f"Cache delete successful for key: {key}")
                return True
            else:
                logger.debug(f"Cache delete: key not found {key}")
                return False
        
        except Exception as e:
            logger.error(f"Redis delete error for key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """
        check if key exists in redis
        """
        try:
            client = await self._get_client()
            if not client:
                logger.error("Redis client not initialized")
                return False
            
            # check existence in redis
            result = await client.exists(key)

            exists = result > 0

            logger.debug(f"Cache exists check for key: {key} - {exists}")
            return exists
        
        except Exception as e:
            logger.error(f"Redis exists error for key {key}: {e}")
            return False
        
    async def clear_pattern(self, pattern: str) -> int:
        """
        delete all keys matching pattern from redis
        """
        try:
            client = await self._get_client()
            if not client:
                logger.error("Redis client not initialized")
                return 0
            
            # finding keys matching pattern
            keys = await client.keys(pattern)

            if not keys:
                logger.debug(f"No keys found for pattern: {pattern}")
                return 0
            
            # delete all matching keys
            deleted_count = await client.delete(*keys)
            logger.debug(f"Cache clear pattern: {pattern}, deleted {deleted_count} keys")
            return deleted_count
        
        except Exception as e:
            logger.error(f"Redis clear_pattern error for pattern {pattern}: {e}")
            return 0
        
    async def get_multiple(self, keys: List[str]) -> Dict[str, Any]:
        """
        get multiple keys at once from redis
        """
        try:
            client = await self._get_client()
            if not client:
                logger.error("Redis client not initialized")
                return {}
            if not keys:
                return {}
            raw_values = await client.mget(keys)
            result = {}
            for key, raw_value in zip(keys, raw_values):
                if raw_value is not None:
                    try:
                        result[key] = self._deserialize_value(raw_value)
                    except Exception as e:
                        logger.error(f"Error deserializing value for key {key}: {e}")

            logger.debug(f"Cache get_multiple for keys: {keys}, found {len(result)} items")
            return result
        
        except Exception as e:
            logger.error(f"Redis get_multiple error for keys {keys}: {e}")
            return {}
        
    
    # ========================================
    # HELPER METHODS (OPTIONAL TO OVERRIDE)
    # ========================================

    async def set_multiple(self, data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """
        set multiple key value pairs at once in redis
        """

        try:
            client = await self._get_client()
            if not client:
                logger.error("Redis client not initialized")
                return False
            
            if not data:
                return True
            
            # serialize all values
            serialized_data = {}
            for key, value in data.items():
                try:
                    serialized_data[key] = self._serialize_value(value)
                except Exception as e:
                    logger.error(f"Error serializing value for key {key}: {e}")
                    return False
                
            
            if ttl:
                # using pipeline for TTL operations
                pipe = client.pipeline()
                for key, value in serialized_data.items():
                    pipe.setex(key, ttl, value)
                
                await pipe.execute()
            
            else:
                # using mset for bulk set without TTL
                await client.mset(serialized_data)
            
            logger.debug(f"Cache set_multiple for keys: {list(data.keys())} with ttl: {ttl}")
            return True

        except Exception as e:
            logger.error(f"Redis set_multiple error for keys {list(data.keys())}: {e}")
            return False
    
    async def get_ttl(self, key: str) -> Optional[int]:
        """
        get remaining TTL (time to live) for a key in seconds
        """
        try:
            client = await self._get_client()
            if not client:
                logger.error("Redis client not initialized")
                return None
            
            ttl = await client.ttl(key)
            return ttl if ttl>0 else None
        
        except Exception as e:
            logger.error(f"Redis get_ttl error for key {key}: {e}")
            return None


    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """
        increment numeric value of a key by amount
        """
        try:
            client = await self._get_client()
            if not client:
                logger.error("Redis client not initialized")
                return None
            new_value = await client.incrby(key, amount)
            logger.debug(f"Cache increment for key: {key} by {amount}, new value: {new_value}")
            return new_value

        except Exception as e:
            logger.error(f"Redis increment error for key {key}: {e}")
            return None
        
    
    async def get_cache_info(self) -> Dict[str, Any]:
        """
        get basic info about the redis cache
        """
        try:
            client = await self._get_client()
            if not client:
                logger.error("Redis client not initialized")
                return {}
            info = await client.info()
            return {
                "redis_version": info.get("redis_version"),
                "used_memory": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "uptime_in_seconds": info.get("uptime_in_seconds")
            }
        
        except Exception as e:
            logger.error(f"Redis get_cache_info error: {e}")
            return {}
        
    # ========================================
    # AI specific methods (OPTIONAL TO OVERRIDE)
    # ========================================

    async def cache_embedding(self, text: str, embedding: List[float], ttl: Optional[int] = None) -> bool:
        """
        cache embedding vector for a key
        """
        key = self.make_key("embedding", text)
        return await self.set(key, embedding, ttl=ttl or redis_config.embedding_ttl)
    
    async def get_cached_embedding(self, text: str) -> Optional[List[float]]:
        """
        get cached embedding vector for a key
        """
        key = self.make_key("embedding", text)
        return await self.get(key)
    
    async def cache_search_results(self, query: str, results: Any) -> bool:
        """
        cache search results for a query
        """
        key = self.make_key("search", query)
        return await self.set(key, results, ttl=redis_config.search_ttl)

    async def get_cached_search_results(self, query: str) -> Optional[Any]:
        """
        get cached search results for a query
        """
        key = self.make_key("search", query)
        return await self.get(key)
    
    async def cache_llm_response(self, prompt: str, response: str) -> bool:
        """
        cache LLM response for a prompt with default TTL
        """
        key = self.make_key("llm", prompt)
        return await self.set(key, response, ttl=redis_config.llm_response_ttl)
    
    async def get_cached_llm_response(self, prompt: str) -> Optional[str]:
        """
        get cached LLM response for a prompt
        """
        key = self.make_key("llm", prompt)
        return await self.get(key)
    
    # =======================================
    # CLEANUP
    # =======================================

    async def close(self):
        """
        close redis connection
        """
        if self._redis_client:
            await self._redis_client.close()
            self._redis_client = None
            logger.info("Redis connection closed")

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            """
            context manager cleanup
            """
            await self.close()
