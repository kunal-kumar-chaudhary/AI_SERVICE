import asyncio
import config
import logging
from cache.redis.redis_cache import RedisCache

logger = logging.getLogger(__name__)

async def test_redis_cache():
    """
    test the redis cache implementation
    """
    logger.info("Starting RedisCache tests...")

    # redis cache instance
    cache = RedisCache()

    try:
        # 1. basic set and get
        logger.info("Testing set and get...")
        success = await cache.set("test:user", {"name": "kunal", "age": 30}, ttl=60)
        if success:
            user = await cache.get("test:user")
            logger.info(f"Retrieved user from cache: {user}")
        else:
            logger.error("Set operation failed.")
        
        # 2. exists check
        logger.info("Testing exists...")
        exists = await cache.exists("test:user")
        logger.info(f"Key exists: {exists}")

        # 3. batch operations
        logger.info("Testing batch set and get...")
        batch_data = {
            "test:item1": "value1",
            "test:item2": {"field": "value2"},
            "test:item3": {"number": 123}
        }

        await cache.set_multiple(batch_data, ttl=30)
        retrieved = await cache.get_multiple(list(batch_data.keys()))
        logger.info(f"Batch retrieved: {retrieved}")

        # 4. AI specific methods
        logger.info("Testing AI specific methods...")

        # cache an embedding
        embedding = [0.1 * i for i in range(128)]
        await cache.cache_embedding("test:embedding1", embedding, ttl=300)

        # retrieve the embedding
        cached_embedding = await cache.get_cached_embedding("test:embedding1")
        logger.info(f"Cached embedding retrieved: {cached_embedding[:5]}...")  # print first 5 values
        
        # 5. clear by pattern
        logger.info("Testing clear by pattern...")
        deleted_count = await cache.clear_pattern("test:*")
        logger.info(f"Deleted {deleted_count} keys matching pattern 'test:*'")

        # 6. cache info
        info = await cache.get_cache_info()
        logger.info(f"Cache info: {info}")

    except Exception as e:
        logger.error(f"Error during RedisCache tests: {e}")

    finally:
        # clean up
        await cache.close()


if __name__ == "__main__":
    asyncio.run(test_redis_cache())

