from app.persistence.models import MessageIn
from app.persistence.mongo import save_message
from app.ws.manager import manager
from app.redis.redis import redis_client
import asyncio
import loguru
import json
import importlib


def format_payload(payload: dict) -> dict | None:
    """Format the incoming payload to match the MessageIn model structure.
    Accept several incoming shapes and return None if the payload can't be normalized.
    Args:
        payload (dict): The incoming message payload.
    Returns:
        dict | None: Formatted payload dictionary or None on error.
    Example:
        Output:
        {
            "tenant_id": str,
            "dev_eui": str,
            "dev_addr": str,
            "payload": dict
        }
    """
    try:
        # Already normalized
        if (
            isinstance(payload, dict)
            and "tenant_id" in payload
            and "dev_eui" in payload
        ):
            return payload

        # Common incoming shape: nested deviceInfo
        device_info = payload.get("deviceInfo") or payload.get("device_info")
        if device_info and isinstance(device_info, dict):
            return {
                "tenant_id": device_info.get("tenantId")
                or device_info.get("tenant_id"),
                "dev_eui": device_info.get("devEui") or device_info.get("dev_eui"),
                "dev_addr": payload.get("devAddr") or payload.get("dev_addr"),
                "payload": payload.get("object") or payload.get("payload") or {},
            }

        # Fallback: try top-level keys that may exist
        if any(k in payload for k in ("devEui", "dev_eui", "devAddr", "dev_addr")):
            return {
                "tenant_id": payload.get("tenantId") or payload.get("tenant_id"),
                "dev_eui": payload.get("devEui") or payload.get("dev_eui"),
                "dev_addr": payload.get("devAddr") or payload.get("dev_addr"),
                "payload": payload.get("object") or payload.get("payload") or {},
            }

        loguru.logger.error("Unexpected payload shape in format_payload: %s", payload)
        return None
    except Exception:
        loguru.logger.exception("Error while formatting payload")
        return None


def handle_message(payload: dict, db, loop):
    """Handle incoming MQTT messages.
    Args:
        payload (dict): The incoming message payload.
        db: The database connection.
    """
    try:
        formatted = format_payload(payload)
        if not formatted:
            loguru.logger.error(
                "Skipping message because payload could not be formatted"
            )
            return

        # Dynamically get redis client to avoid None at import-time
        redis_mod = importlib.import_module("app.redis.redis")
        client = getattr(redis_mod, "redis_client", None)
        if client is None:
            loguru.logger.error("Redis client not initialized, skipping redis push")
        else:
            asyncio.run_coroutine_threadsafe(
                client.lpush("messages", json.dumps(formatted)), loop
            )

        tenant_id = formatted.get("tenant_id") or formatted.get("tenantId")
        if not tenant_id:
            loguru.logger.error(
                "No tenant_id available in formatted payload, skipping broadcast"
            )
            return

        asyncio.run_coroutine_threadsafe(manager.broadcast(formatted, tenant_id), loop)
        loguru.logger.info(f"Message broadcasted to tenant {tenant_id}")

    except Exception:
        loguru.logger.exception("Failed to handle message")


def handle_uplink(payload):
    dev_eui = payload.get("devEui") or payload.get("dev_eui")
    tenant_id = payload.get("tenantId") or payload.get("tenant_id")
    if dev_eui and tenant_id and redis_client:
        try:
            redis_client.hset("device_tenant_mapping", dev_eui, tenant_id)
        except Exception:
            # optional: log
            pass
