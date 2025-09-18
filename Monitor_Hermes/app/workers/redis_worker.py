import asyncio
import json
import loguru
import importlib
from app.persistence.models import MessageIn
from app.persistence.mongo import save_message


async def process_messages(db):
    while True:
        try:
            # get redis client at runtime (may be set by connect_to_redis)
            redis_mod = importlib.import_module("app.redis.redis")
            client = getattr(redis_mod, "redis_client", None)
            if client is None:
                loguru.logger.error("Redis client not initialized, retrying in 1s")
                await asyncio.sleep(1)
                continue

            _, raw = await client.brpop("messages")
            payload = json.loads(raw)

            message = MessageIn(
                tenant_id=payload["deviceInfo"]["tenantId"],
                device_id=payload["deviceInfo"]["devEui"],
                dev_addr=payload["devAddr"],
                payload=payload["object"],
                metadata=(
                    {"deviceProfileId": payload["deviceInfo"]["deviceProfileId"]}
                    if "deviceProfileId" in payload["deviceInfo"]
                    else {}
                ),
            )
            await save_message(db, message)
            loguru.logger.info(
                f"Message saved to database for device {message.device_id} in tenant {message.tenant_id}"
            )
        except Exception as e:
            loguru.logger.error(f"Failed to process message: {e}")
        await asyncio.sleep(1)
