"""
Device-to-user mapping utilities.
Implements hybrid caching strategy: Redis (L1) -> MongoDB (L2) -> Atlas API (Source).
"""

from typing import Optional, List
import json
from datetime import datetime, timezone
import loguru
import httpx

from app.persistence.models import DeviceUserMapping
from app.persistence.mongo import get_users_for_device, save_device_user_mapping
from app.redis.redis import get_redis_client
from app.clients.atlas import atlas_client

REDIS_TTL = 7200  # 2 hours


async def get_device_user_mapping(db, dev_eui: str) -> Optional[DeviceUserMapping]:
    """
    Get device-user mapping with multi-level caching strategy.

    Flow:
    1. Check Redis cache
    2. Check MongoDB
    3. Fetch from Atlas API
    4. Save to Mongo & Redis if found
    """
    redis_key = f"device_user_map:{dev_eui}"

    # 1. Try Redis
    try:
        redis_client = get_redis_client()
        cached_data = await redis_client.get(redis_key)
        if cached_data:
            loguru.logger.debug(f"Cache HIT (Redis) for {dev_eui}")
            return DeviceUserMapping(**json.loads(cached_data))
    except Exception as e:
        loguru.logger.warning(f"Redis error reading mapping for {dev_eui}: {e}")

    # 2. Try MongoDB
    mapping = await get_users_for_device(db, dev_eui)
    if mapping:
        loguru.logger.debug(f"Cache HIT (Mongo) for {dev_eui}")
        # Populate Redis asynchronously
        await _cache_mapping_in_redis(mapping)
        return mapping

    # 3. Fetch from Atlas API
    loguru.logger.info(f"Cache MISS for {dev_eui}. Fetching from Atlas...")
    try:
        response = await atlas_client.get(
            "/api/v1/infrastructure/device/get_users_for_device",
            params={"dev_eui": dev_eui},
            timeout=5.0,
        )

        data = response.json()

        # Transform Atlas response to our model
        # Atlas returns: {"dev_eui": "...", "tenant_id": "...", "assigned_users": [{"user_id": "...", ...}]}
        # We need list of strings for assigned_users

        assigned_users_list = [
            u.get("user_id") for u in data.get("assigned_users", []) if u.get("user_id")
        ]

        new_mapping = DeviceUserMapping(
            dev_eui=data.get("dev_eui", dev_eui),
            tenant_id=str(data.get("tenant_id", "")),
            assigned_users=[str(uid) for uid in assigned_users_list],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        # 4. Save to Mongo & Redis
        await save_device_user_mapping(db, new_mapping)
        await _cache_mapping_in_redis(new_mapping)

        loguru.logger.info(f"Fetched and cached mapping for {dev_eui}")
        return new_mapping

    except httpx.HTTPError as e:
        loguru.logger.warning(f"Atlas API error fetching mapping for {dev_eui}: {e}")
    except Exception as e:
        loguru.logger.exception(f"Unexpected error fetching mapping for {dev_eui}: {e}")

    return None


async def update_device_user_mapping_cache(db, mapping: DeviceUserMapping):
    """
    Update mapping in both MongoDB and Redis.
    Used by synchronization endpoints.
    """
    await save_device_user_mapping(db, mapping)
    await _cache_mapping_in_redis(mapping)
    loguru.logger.info(f"Updated mapping for {mapping.dev_eui} (Mongo + Redis)")


async def _cache_mapping_in_redis(mapping: DeviceUserMapping):
    """Helper to save mapping to Redis with TTL."""
    try:
        redis_client = get_redis_client()
        redis_key = f"device_user_map:{mapping.dev_eui}"
        # Serialize with model_dump_json() for Pydantic v2 compatibility
        await redis_client.set(redis_key, mapping.model_dump_json(), ex=REDIS_TTL)
    except Exception as e:
        loguru.logger.error(f"Failed to cache mapping in Redis: {e}")


# --- Legacy/Helper wrappers using the new logic ---


async def get_user_ids_for_alert(db, dev_eui: str, tenant_id: str) -> List[str]:
    """Get user IDs to notify for a device alert using hybrid cache."""
    mapping = await get_device_user_mapping(db, dev_eui)

    if mapping:
        return mapping.assigned_users if mapping.assigned_users else []

    return []
