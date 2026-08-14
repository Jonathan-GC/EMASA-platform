import sys
import time
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
    logger.debug("Connected to Redis")
    logger.debug(f"[connect_to_redis] redis_client id: {id(redis_client)}")
    logger.debug(f"[connect_to_redis] modules: {list(sys.modules.keys())}")


async def close_redis_connection():
    global redis_client
    if redis_client:
        await redis_client.close()


def get_redis_client() -> aioredis.Redis:
    """
    Get the Redis client instance.
    Raises RuntimeError if Redis is not connected.
    """
    if redis_client is None:
        raise RuntimeError("Redis is not connected. Call connect_to_redis() first.")
    return redis_client


async def check_redis_health() -> dict:
    """Check Redis connection health and measure latency."""
    global redis_client
    if redis_client is None:
        return {
            "status": "unhealthy",
            "error": "Redis client is not connected",
        }
    start = time.perf_counter()
    try:
        pong = await redis_client.ping()
        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        if pong:
            return {
                "status": "healthy",
                "latency_ms": latency_ms,
            }
        return {
            "status": "unhealthy",
            "latency_ms": latency_ms,
            "error": "Ping command returned false",
        }
    except Exception as e:
        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.warning(f"Redis healthcheck failed: {e}")
        return {
            "status": "unhealthy",
            "latency_ms": latency_ms,
            "error": str(e),
        }

