"""
Rate limiting for alerts using Redis.
Prevents alert spam from repeated violations.
"""

import loguru
from app.redis.redis import get_redis_client


async def should_send_alert(dev_eui: str, unit: str) -> bool:
    """
    Check if alert should be sent based on cooldown period.
    Returns True if alert can be sent, False if in cooldown.
    Uses Redis key with 5 minute TTL.
    """
    key = f"alert_cooldown:{dev_eui}:{unit}"

    try:
        redis_client = get_redis_client()
        exists = await redis_client.exists(key)

        if exists:
            loguru.logger.debug(f"Alert cooldown active for {dev_eui}:{unit}")
            return False

        await redis_client.setex(key, 60, "1")
        return True

    except Exception as e:
        loguru.logger.exception(f"Redis error checking cooldown: {e}")
        return True
