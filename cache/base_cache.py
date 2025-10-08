"""
Defines the interface and base functionality for various cache implementations.
This ensures consistency across different cache backends (e.g., Redis, in-memory, file-based)
by establishing clear contracts about:
    - what operations any cache should support
    - how those operations should behave
    - what parameters they should accept
    - what they should return
"""

from abc import ABC, abstractmethod
from typing import Optional, Any, List, Dict, Union
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class CacheError(Exception):
    """Base exception for cache errors"""
    pass

class BaseCache(ABC):
    """
    Simple abstract base class for cache implementations.
    
    Any cache (Redis, Memory, etc.) must implement these 6 core methods.
    """
    
    # ========================================
    # CORE METHODS (MUST IMPLEMENT)
    # ========================================
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value by key. Returns None if not found."""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set key-value pair. ttl in seconds. Returns True if successful."""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete key. Returns True if key existed."""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        pass
    
    @abstractmethod
    async def clear_pattern(self, pattern: str) -> int:
        """Delete keys matching pattern. Returns number of deleted keys."""
        pass
    
    @abstractmethod
    async def get_multiple(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple keys at once. Returns dict of found key-value pairs."""
        pass
    
    # ========================================
    # HELPER METHODS (OPTIONAL TO OVERRIDE)
    # ========================================
    
    def make_key(self, namespace: str, identifier: str) -> str:
        """Create a cache key: namespace:identifier"""
        return f"{namespace}:{identifier}"
    
    async def get_or_none(self, key: str) -> Optional[Any]:
        """Get value, return None on any error (useful for fallback)"""
        try:
            return await self.get(key)
        except Exception as e:
            logger.warning(f"Cache get failed for key {key}: {e}")
            return None
    
    async def set_safe(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value, return False on any error (useful for fallback)"""
        try:
            return await self.set(key, value, ttl)
        except Exception as e:
            logger.warning(f"Cache set failed for key {key}: {e}")
            return False