from app.persistence.models import MessageIn
from app.persistence.mongo import save_message
from app.ws.manager import manager
from app.redis.redis import redis_client
import asyncio
import loguru
import json
import importlib


def format_payload(payload: dict) -> dict:
    """Format the incoming payload to match the MessageIn model structure.
    Args:
        payload (dict): The incoming message payload.
    Returns:
        dict: Formatted payload dictionary.
    """
    return payload  # Currently, no changes are made; this is a placeholder for future formatting.


def handle_message(payload: dict, db, loop):
    """Handle incoming MQTT messages.
    Args:
        payload (dict): The incoming message payload.
        db: The database connection.
    """
    try:
        payload = format_payload(payload)

        # Dynamically get redis client to avoid None at import-time
        redis_mod = importlib.import_module("app.redis.redis")
        client = getattr(redis_mod, "redis_client", None)
        if client is None:
            loguru.logger.error("Redis client not initialized, skipping redis push")
        else:
            asyncio.run_coroutine_threadsafe(
                client.lpush("messages", json.dumps(payload)), loop
            )

        tenant_id = payload["deviceInfo"]["tenantId"]
        asyncio.run_coroutine_threadsafe(manager.broadcast(payload, tenant_id), loop)
        loguru.logger.info(f"Message broadcasted to tenant {tenant_id}")

    except Exception as e:
        loguru.logger.error(f"Failed to handle message: {e}")
