import os
import redis
import redis.asyncio as aioredis
import logging
from typing import Optional
from dotenv import load_dotenv
from . import *

load_dotenv()
logger = logging.getLogger(__name__)

class RedisConfig:
    """
    Configuration class for Redis settings
    """

    def __init__(self):

        # Basic connection parameters
        self.host = os.getenv("REDIS_HOST", "localhost")
        self.port = int(os.getenv("REDIS_PORT", 6379))
        self.db = int(os.getenv("REDIS_DB", 0))
        self.password = os.getenv("REDIS_PASSWORD") or None

        # connection pool settings
        self.max_connections = int(os.getenv("REDIS_MAX_CONNECTIONS", 20)) # max connections to redis
        self.socket_timeout = int(os.getenv("REDIS_SOCKET_TIMEOUT", 5)) # how long to wait for response
        self.socket_connect_timeout = int(os.getenv("REDIS_SOCKET_CONNECT_TIMEOUT", 5)) # connection timeout

        self.retry_on_timeout = True # retry if redis doesn't respond
        self.decode_responses = True # convert redis bytes to strings automatically

        # cache expiration times
        self.embedding_ttl = int(os.getenv("CACHE_EMBEDDING_TTL", 3600))     # 1 hour
        self.search_ttl = int(os.getenv("CACHE_SEARCH_TTL", 1800))           # 30 minutes
        self.llm_response_ttl = int(os.getenv("CACHE_LLM_TTL", 7200))        # 2 hours
        self.triplets_ttl = int(os.getenv("CACHE_TRIPLETS_TTL", 3600))       # 1 hour


# global instance of the config
redis_config = RedisConfig()

def get_redis_connection() -> Optional[redis.Redis]:
    """
    creates a synchronous Redis connection
    returns:
        - Redis client or None of connection fails
    """
    try:
        logger.info(f"Connecting to Redis at {redis_config.host}:{redis_config.port}, DB: {redis_config.db}")
        pool_kwargs = {
            'host': redis_config.host,
            'port': redis_config.port,
            'db': redis_config.db,
            'max_connections': redis_config.max_connections,
            'socket_timeout': redis_config.socket_timeout,
            'socket_connect_timeout': redis_config.socket_connect_timeout,
            'retry_on_timeout': redis_config.retry_on_timeout,
            'decode_responses': redis_config.decode_responses
        }

        # Only add password if it's set
        if redis_config.password:
            pool_kwargs['password'] = redis_config.password
            logger.info("Using Redis password authentication")
        else:
            logger.info("Connecting to Redis without password")
        
        pool = redis.ConnectionPool(**pool_kwargs)
        # creating redis client using the pool
        redis_client = redis.Redis(connection_pool=pool)

        # testing the connection
        redis_client.ping()
        logger.info("Successfully connected to Redis!")

        return redis_client
    
    except redis.ConnectionError as e:
        logger.error(f"Failed to connect to Redis: {e}")
        logger.info("Please ensure that the Redis server is running and accessible.")
        return None
    
    except Exception as e:
        logger.error(f"Unexpected error connecting to Redis: {e}")
        return None
    

async def get_async_redis_connection() -> Optional[aioredis.Redis]:
    """
    creates an asynchronous Redis connection
    returns:
        - async redis client or None if connection fails
    """

    try:
        logger.info(f"Connecting to Async Redis at {redis_config.host}:{redis_config.port}, DB: {redis_config.db}")

        redis_kwargs = {
            'host': redis_config.host,
            'port': redis_config.port,
            'db': redis_config.db,
            'socket_timeout': redis_config.socket_timeout,
            'socket_connect_timeout': redis_config.socket_connect_timeout,
            'decode_responses': redis_config.decode_responses
        }
        
        # Only add password if it exists
        if redis_config.password:
            redis_kwargs['password'] = redis_config.password
            logger.info("Using async Redis password authentication")
        else:
            logger.info("Connecting to async Redis without password")
        redis_client = aioredis.Redis(**redis_kwargs)

        # testing connection
        await redis_client.ping()
        logger.info("Successfully connected to Async Redis!")
        return redis_client
    
    except aioredis.ConnectionError as e:
        logger.error(f"Failed to connect to Async Redis: {e}")
        logger.info("Please ensure that the Redis server is running and accessible.")
        return None

    except Exception as e:
        logger.error(f"Unexpected error connecting to Async Redis: {e}")
        return None

def test_redis_connection() -> bool:
    """
    Simple function to test if Redis is working
    Call this to check if everything is set up correctly

    Returns:
        True if Redis is working, False otherwise
    """

    try:
        logger.info("Testing Redis connection...")
        
        # Get Redis client
        client = get_redis_connection()
        if not client:
            return False
        
        # Try some basic operations
        client.set("test_key", "test_value")        # Storing something
        value = client.get("test_key")              # Retrieving it
        client.delete("test_key")                   # Cleaning up

        if value == "test_value":
            logger.info("Redis test successful! All operations working.")
            return True
        else:
            logger.error("Redis test failed: Could not retrieve test value")
            return False
            
    except Exception as e:
        logger.error(f"Redis test failed with error: {e}")
        return False
    

async def test_async_redis_connection() -> bool:
    """
    Test async Redis connection
    
    Returns:
        True if async Redis is working, False otherwise
    """
    try:
        logger.info("Testing async Redis connection...")
        
        # Get async Redis client
        client = await get_async_redis_connection()
        if not client:
            return False
        
        # Trying some basic operations
        await client.set("async_test_key", "async_test_value")
        value = await client.get("async_test_key")
        await client.delete("async_test_key")

        # Close the connection
        await client.close()
        
        if value == "async_test_value":
            logger.info("Async Redis test successful!")
            return True
        else:
            logger.error("Async Redis test failed: Could not retrieve test value")
            return False
            
    except Exception as e:
        logger.error(f"Async Redis test failed with error: {e}")
        return False


# helper function to get redis info
def get_redis_info() -> Optional[dict]:
    """
    get information about the redis server
    
    returns:
        - dictionary with redis server information
    """
    try:
        client = get_redis_connection()
        if client:
            info = client.info()
            logger.info("Retrieved Redis server info successfully.")
            return {
                "redis_version": info.get("redis_version"),
                "used_memory": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "uptime_in_seconds": info.get("uptime_in_seconds"),
                "keyspace": info.get("db0", {})
            }
    except Exception as e:
        logger.info(f"Error retrieving Redis info: {e}")
        return None
    return None

