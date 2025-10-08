import functools
import logging
import hashlib
from typing import Optional, Callable, Any
from ..cache.base_cache import BaseCache

logger = logging.getLogger(__name__)

def cache_result(ttl: Optional[int] = None, key_prefix: str = "cache"):
    """
    simple decorator to cache function results

    usage:
        @cache_result(ttl=3600, key_prefix="embedding")
        async def get_embedding(self, text: str):
            return expensive_computation(text)
    
    args:
        ttl: time to live for the cache entry in seconds
        key_prefix: prefix to use for the cache key (e.g., "embedding", "search", "llm")

    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs):
            # get the cache from self (assuming self.cache exists)
            cache: BaseCache = getattr(self, "cache", None)
            if not cache:
                logger.warning(f"no cache found on {self.__class__.__name__}, executing without cache")
                return await func(self, *args, **kwargs)
            
            # generating cache key from function arguments
            cache_key = _make_cache_key(key_prefix, func.__name__, args, kwargs)

            # trying to get from cache
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"cache hit for key: {cache_key}")
                return cached_value

            # cache miss, calling the actual function
            logger.debug(f"cache miss for key: {cache_key}, calling function")
            result = await func(self, *args, **kwargs)

            # storing the result in cache
            if result is not None:
                await cache.set(cache_key, result, ttl=ttl)
            
            return result
        return wrapper
    return decorator


def invalidate_cache_pattern(pattern: str):
    """
    decorator to invalidate cache after function runs
    
    usage:
        @invalidate_cache_pattern("embedding:*")
        async def update_embedding(self, text: str):
            # after this runs, all embedding keys are deleted
    
    args:
        pattern: cache key pattern to delete (e.g., "embedding:*")
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs):
            # executing the function first
            result = await func(self, *args, **kwargs)

            # then invalidating the cache
            cache: BaseCache = getattr(self, "cache", None)
            if cache:
                deleted = await cache.clear_pattern(pattern)
                logger.info(f"invalidated {deleted} cache entries matching pattern: {pattern}")
            
            return result
        return wrapper
    return decorator

def cache_if(condition: Callable[[Any], bool], ttl: Optional[int] = None, key_prefix: str = "cache"):
    """
    cache result only if condition is met
    
    usage:
        @cache_if(lambda self, text: len(text) > 10, ttl=3600, key_prefix="embedding")
        async def get_embedding(self, text: str):
            # only caches if length of text > 10
            return expensive_computation(text)
    
    args:
        condition: function that takes same args as decorated function and returns bool
        ttl: time to live for the cache entry in seconds
        key_prefix: prefix to use for the cache key (e.g., "embedding", "search", "llm")

    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs):
            # evaluating the condition
            should_cache = condition(self, *args, **kwargs)
            if not should_cache:
                logger.debug("condition for caching not met, executing without cache")
                return await func(self, *args, **kwargs)
            
            # usinf cache
            cache: BaseCache = getattr(self, "cache", None)
            if not cache:
                logger.warning(f"no cache found on {self.__class__.__name__}, executing without cache")
                return await func(self, *args, **kwargs)
            
            cache_key = _make_cache_key(key_prefix, func.__name__, args, kwargs)

            # tring to cache
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"cache hit for key: {cache_key}")
                return cached_value
            
            # execute and cache
            result = await func(self, *args, **kwargs)
            if result is not None:
                await cache.set(cache_key, result, ttl=ttl)

            return result
        return wrapper
    return decorator

async def _make_cache_key(prefix: str, func_name: str, args: tuple, kwargs: dict) -> str:
    """
    create a unqiue cache key based on function name and arguments

    example:
        prefix: "embedding", func="get_embedding", args=("some text",), kwargs={"model": "text-embedding-ada-002"}
        returns: "embedding:get_embedding:5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8"
    """

    # converting args and kwargs to a string representation
    args_str = str(args) + str(sorted(kwargs.items()))

    # hashing it
    args_hash = hashlib.md5(args_str.encode()).hexdigest()[:16]

    # building the key
    return f"{prefix}:{func_name}:{args_hash}"
