import asyncio
import json
import loguru
import importlib
from app.persistence.models import MessageIn
from app.persistence.mongo import save_message


async def save_mapping(dev_eui: str, tenant_id: str, redis_client):
    try:
        await redis_client.hset("device_tenant_mapping", dev_eui, tenant_id)
    except Exception:
        loguru.logger.exception("Failed to save device_tenant_mapping")


async def process_messages(db):
    """Process messages from Redis queue."""
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

            # Expected structure (snake_case):
            # {
            #   "tenant_id": str,
            #   "dev_eui": str,
            #   "dev_addr": str | None,
            #   "device_name": str | None,
            #   "frequency": int | None,
            #   "f_cnt": int | None,
            #   "region": str | None,
            #   "payload": dict,
            #   "metadata": dict | None
            # }

            dev_eui = payload.get("dev_eui")
            tenant_id = payload.get("tenant_id")
            dev_addr = payload.get("dev_addr")
            device_name = payload.get("device_name")
            frequency = payload.get("frequency")
            f_cnt = payload.get("f_cnt")
            region = payload.get("region")
            object_payload = payload.get("payload", {})
            metadata = payload.get("metadata")

            if not dev_eui or not tenant_id:
                loguru.logger.warning(
                    f"Skipping message without dev_eui or tenant_id: {payload}"
                )
                await asyncio.sleep(1)
                continue

            if dev_eui and tenant_id:
                await save_mapping(dev_eui, tenant_id, client)

            loguru.logger.debug(f"Processing message from Redis: {dev_eui}")

            message = MessageIn(
                tenant_id=tenant_id,
                device_id=dev_eui,
                dev_addr=dev_addr,
                device_name=device_name,
                frequency=frequency,
                f_cnt=f_cnt,
                region=region,
                payload=object_payload,
                metadata=metadata,
            )

            loguru.logger.debug(
                f"Message created for device {message.device_id} in tenant {message.tenant_id}"
            )

            await save_message(db, message)
            loguru.logger.debug(
                f"Message saved to database for device {message.device_id} in tenant {message.tenant_id}"
            )

            try:
                ws_mod = importlib.import_module("app.ws.manager")
                ws_manager = getattr(ws_mod, "manager", None)
                if ws_manager is not None and dev_eui:
                    ws_payload = {
                        "type": "uplink",
                        "tenant_id": tenant_id,
                        "dev_eui": dev_eui,
                        "dev_addr": dev_addr,
                        "device_name": device_name,
                        "frequency": frequency,
                        "f_cnt": f_cnt,
                        "region": region,
                        "payload": object_payload,
                    }
                    await ws_manager.broadcast_to_device(ws_payload, dev_eui)
                    loguru.logger.debug(f"Notified device subscribers for {dev_eui}")
            except Exception:
                loguru.logger.exception("Failed to notify WS subscribers for device")

        except Exception as e:
            loguru.logger.error(f"Failed to process message: {e}")

        await asyncio.sleep(1)
