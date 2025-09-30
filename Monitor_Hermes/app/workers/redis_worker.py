import asyncio
import json
import loguru
import importlib
from app.persistence.models import MessageIn
from app.persistence.mongo import save_message


def _normalize_payload(payload: dict) -> dict:
    """Normalize incoming payload to a consistent shape used by the worker."""
    if not isinstance(payload, dict):
        return payload

    # Already normalized by handlers.format_payload
    if "tenant_id" in payload and "dev_eui" in payload:
        return {
            "tenantId": payload.get("tenant_id"),
            "devEui": payload.get("dev_eui"),
            "devAddr": payload.get("dev_addr") or payload.get("devAddr"),
            "object": payload.get("payload") or payload.get("object") or {},
            "deviceProfileId": payload.get("device_profile_id")
            or payload.get("deviceProfileId"),
        }

    # legacy shape with nested deviceInfo
    device_info = payload.get("deviceInfo") or payload.get("device_info")
    if isinstance(device_info, dict):
        return {
            "deviceInfo": device_info,
            "devAddr": payload.get("devAddr") or payload.get("dev_addr"),
            "object": payload.get("object") or payload.get("payload") or {},
        }

    # try to normalize top-level keys if present
    if any(k in payload for k in ("devEui", "dev_eui", "devAddr", "dev_addr")):
        return {
            "tenantId": payload.get("tenantId") or payload.get("tenant_id"),
            "devEui": payload.get("devEui") or payload.get("dev_eui"),
            "devAddr": payload.get("devAddr") or payload.get("dev_addr"),
            "object": payload.get("object") or payload.get("payload") or {},
            "deviceProfileId": payload.get("deviceProfileId")
            or payload.get("device_profile_id"),
        }

    return payload


async def process_messages(db):
    while True:
        try:
            redis_mod = importlib.import_module("app.redis.redis")
            client = getattr(redis_mod, "redis_client", None)
            if client is None:
                loguru.logger.error("Redis client not initialized, retrying in 1s")
                await asyncio.sleep(1)
                continue

            _, raw = await client.brpop("messages")
            payload = json.loads(raw)
            payload = _normalize_payload(payload)

            # extract identifiers from normalized payload
            dev_eui = None
            tenant_id = None
            dev_addr = None
            metadata = {}

            if "deviceInfo" in payload and isinstance(payload["deviceInfo"], dict):
                device_info = payload["deviceInfo"]
                dev_eui = device_info.get("devEui") or device_info.get("dev_eui")
                tenant_id = device_info.get("tenantId") or device_info.get("tenant_id")
                if "deviceProfileId" in device_info:
                    metadata = {"deviceProfileId": device_info.get("deviceProfileId")}
            else:
                dev_eui = payload.get("devEui") or payload.get("dev_eui")
                tenant_id = payload.get("tenantId") or payload.get("tenant_id")
                if "deviceProfileId" in payload:
                    metadata = {"deviceProfileId": payload.get("deviceProfileId")}

            dev_addr = payload.get("devAddr") or payload.get("dev_addr")
            object_payload = payload.get("object") or payload.get("payload") or {}

            loguru.logger.info(f"Processing message from Redis: {dev_eui}")

            message = MessageIn(
                tenant_id=tenant_id,
                device_id=dev_eui,
                dev_addr=dev_addr,
                payload=object_payload,
                metadata=metadata,
            )
            loguru.logger.info(
                f"Message created for device {message.device_id} in tenant {message.tenant_id}"
            )
            await save_message(db, message)
            loguru.logger.info(
                f"Message saved to database for device {message.device_id} in tenant {message.tenant_id}"
            )
            # try to notify websocket subscribers for this device on this instance
            try:
                ws_mod = importlib.import_module("app.ws.manager")
                ws_manager = getattr(ws_mod, "manager", None)
                if ws_manager is not None and dev_eui:
                    # prepare a small payload for websockets
                    ws_payload = {
                        "type": "uplink",
                        "tenantId": tenant_id,
                        "devEui": dev_eui,
                        "devAddr": dev_addr,
                        "object": object_payload,
                    }
                    await ws_manager.broadcast_to_device(ws_payload, dev_eui)
            except Exception:
                loguru.logger.exception("Failed to notify WS subscribers for device")
        except Exception as e:
            loguru.logger.error(f"Failed to process message: {e}")
        await asyncio.sleep(1)
