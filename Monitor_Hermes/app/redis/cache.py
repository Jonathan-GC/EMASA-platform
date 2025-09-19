from .redis import redis_client

DEFAULT_TTL = 300  # Default time-to-live for cache entries in seconds


async def cache_devEui_mapping(dev_eui: str, tenant_id: str):
    key = f"devEui:{dev_eui}"
    await redis_client.set(key, tenant_id, ex=DEFAULT_TTL)


async def get_devEui_mapping(dev_eui: str) -> str | None:
    key = f"devEui:{dev_eui}"
    return await redis_client.get(key)
