from app.persistence.models import MessageIn
from app.persistence.mongo import save_message
from app.ws.manager import manager
from app.redis.redis import get_redis_client
import asyncio
import loguru
import json


def format_payload(payload: dict) -> dict | None:
    """Format the incoming payload to match the MessageIn model structure.
    Accept several incoming shapes and return None if the payload can't be normalized.

    This is the SINGLE normalization point. The output is used for:
    - Broadcasting to websockets (immediate)
    - Pushing to Redis queue
    - Persistence in MongoDB (via worker)

    Args:
        payload (dict): The incoming message payload.
    Returns:
        dict | None: Formatted payload dictionary or None on error.
    Example:
        Output (snake_case for consistency):
        {
            "tenant_id": str,
            "dev_eui": str,
            "dev_addr": str | None,
            "device_name": str | None,
            "frequency": int | None,
            "f_cnt": int | None,
            "region": str | None,
            "payload": dict,
            "metadata": dict | None
        }
    """
    try:
        # Already normalized (trust it and return as-is)
        if (
            isinstance(payload, dict)
            and "tenant_id" in payload
            and "dev_eui" in payload
        ):
            return payload

        formatted_payload = {}

        device_info = payload.get("deviceInfo") or payload.get("device_info")
        if device_info and isinstance(device_info, dict):
            formatted_payload["dev_eui"] = device_info.get("devEui") or device_info.get(
                "dev_eui"
            )
            formatted_payload["tenant_id"] = device_info.get(
                "tenantId"
            ) or device_info.get("tenant_id")
            formatted_payload["tenant_name"] = device_info.get(
                "tenantName"
            ) or device_info.get("tenant_name")
            formatted_payload["device_name"] = device_info.get(
                "deviceName"
            ) or device_info.get("device_name")

            device_profile_id = device_info.get("deviceProfileId") or device_info.get(
                "device_profile_id"
            )
            if device_profile_id:
                formatted_payload["metadata"] = {"device_profile_id": device_profile_id}
        else:
            # Fallback: try top-level keys
            formatted_payload["dev_eui"] = payload.get("devEui") or payload.get(
                "dev_eui"
            )
            formatted_payload["tenant_id"] = payload.get("tenantId") or payload.get(
                "tenant_id"
            )
            formatted_payload["device_name"] = payload.get("deviceName") or payload.get(
                "device_name"
            )

        tx_info = payload.get("txInfo")
        formatted_payload["frequency"] = (
            tx_info.get("frequency")
            if isinstance(tx_info, dict) and "frequency" in tx_info
            else None
        )

        formatted_payload["dev_addr"] = payload.get("devAddr") or payload.get(
            "dev_addr"
        )
        formatted_payload["f_cnt"] = payload.get("fCnt") or payload.get("f_cnt")
        formatted_payload["region"] = payload.get("regionConfigId") or payload.get(
            "region_config_id"
        )
        formatted_payload["payload"] = (
            payload.get("object") or payload.get("payload") or {}
        )
        if "metadata" not in formatted_payload:
            formatted_payload["metadata"] = None

        if not formatted_payload.get("tenant_id") or not formatted_payload.get(
            "dev_eui"
        ):
            loguru.logger.error(
                "Missing required fields (tenant_id or dev_eui) in payload"
            )
            return None

        return formatted_payload

    except (KeyError, TypeError, AttributeError) as e:
        loguru.logger.exception(f"Error while formatting payload: {e}")
        return None
    except Exception as e:
        loguru.logger.exception(f"Unexpected error while formatting payload: {e}")
        raise


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

        try:
            client = get_redis_client()
            asyncio.run_coroutine_threadsafe(
                client.lpush("messages", json.dumps(formatted)), loop
            )
        except RuntimeError:
            loguru.logger.error("Redis client not initialized, skipping redis push")

        tenant_id = formatted.get("tenant_id") or formatted.get("tenantId")
        if not tenant_id:
            loguru.logger.error(
                "No tenant_id available in formatted payload, skipping broadcast"
            )
            return

        asyncio.run_coroutine_threadsafe(manager.broadcast(formatted, tenant_id), loop)
        loguru.logger.debug(f"Message broadcasted to tenant {tenant_id}")

    except Exception:
        loguru.logger.exception("Failed to handle message")


def handle_uplink(payload):
    dev_eui = payload.get("devEui") or payload.get("dev_eui")
    tenant_id = payload.get("tenantId") or payload.get("tenant_id")
    if dev_eui and tenant_id:
        try:
            client = get_redis_client()
            client.hset("device_tenant_mapping", dev_eui, tenant_id)
        except RuntimeError:
            loguru.logger.error("Redis client not initialized")
        except Exception:
            loguru.logger.exception("Failed to update device-tenant mapping in Redis")
