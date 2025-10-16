from app.redis.redis import redis_client
from loguru import logger
import importlib


async def get_devEui_mapping(dev_eui: str) -> str:
    """
    Given a dev_eui, return the associated tenant_id if exists.
    """
    redis_mod = importlib.import_module("app.redis.redis")
    client = getattr(redis_mod, "redis_client", None)
    if client is None:
        logger.error("Redis client not initialized")
        return None

    try:
        tenant_id = await client.hget("device_tenant_mapping", dev_eui)
        logger.debug(f"[get_devEui_mapping] tenant_id: {tenant_id}")
    except Exception as e:
        logger.exception("Redis hget failed for %s", dev_eui)
        return None

    if tenant_id:
        return (
            tenant_id.decode("utf-8")
            if isinstance(tenant_id, (bytes, bytearray))
            else str(tenant_id)
        )
    return None
