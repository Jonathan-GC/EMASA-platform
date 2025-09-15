import redis.asyncio as aioredis
from app.settings import settings

redis_client: aioredis.Redis | None = None


async def connect_to_redis():
    global redis_client
    redis_client = aioredis.from_url(
        settings.redis_uri,
        decode_responses=True,
    )

    await redis_client.set("healthcheck", "ok", ex=10)


async def close_redis_connection():
    global redis_client
    if redis_client:
        await redis_client.close()
