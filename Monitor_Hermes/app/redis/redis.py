import sys
import redis.asyncio as aioredis
from app.settings import settings
from loguru import logger

redis_client: aioredis.Redis | None = None


async def connect_to_redis():
    global redis_client
    redis_client = aioredis.from_url(
        settings.redis_uri,
        decode_responses=True,
    )

    await redis_client.set("healthcheck", "ok", ex=10)
    logger.info("Connected to Redis")
    logger.info(f"[connect_to_redis] redis_client id: {id(redis_client)}")
    logger.info(f"[connect_to_redis] modules: {list(sys.modules.keys())}")


async def close_redis_connection():
    global redis_client
    if redis_client:
        await redis_client.close()
