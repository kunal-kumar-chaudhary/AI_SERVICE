import asyncio
import json
import config
import logging

from config.redis_config import get_redis_info, test_async_redis_connection, test_redis_connection

logger = logging.getLogger(__name__)

def main():
    
    if test_redis_connection():
        logger.info("sync redis working")
    else:
        logger.error("sync redis not working")
    
    async def test_async():
        if await test_async_redis_connection():
            logger.info("async redis working")
        else:
            logger.error("async redis not working")

    asyncio.run(test_async())

    # getting redis info
    info = get_redis_info()

    if info:
        logger.info(f"redis version: {info.get('redis_version')}")
        logger.info(f"memory used: {info.get('used_memory_human')}")

if __name__ == "__main__":
    main()
