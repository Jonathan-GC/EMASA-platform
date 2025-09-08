from app.persistence.models import MessageIn
from app.persistence.mongo import save_message
import asyncio
import loguru


def handle_message(payload: dict, db, loop):
    """Handle incoming MQTT messages.
    Args:
        payload (dict): The incoming message payload.
        db: The database connection.
    """
    try:
        message = MessageIn(
            tenant_id=payload["deviceInfo"]["tenantId"],
            device_id=payload["deviceInfo"]["devEui"],
            payload=payload["object"],
            metadata=(
                {"deviceProfileId": payload["deviceInfo"]["deviceProfileId"]}
                if "deviceProfileId" in payload["deviceInfo"]
                else {}
            ),
        )
        future = asyncio.run_coroutine_threadsafe(save_message(db, message), loop)
        try:
            future.result()  # Wait for the result to ensure completion
            loguru.logger.info(
                f"Message saved to database for device {message.device_id} in tenant {message.tenant_id}"
            )
        except Exception as e:
            loguru.logger.error(f"Failed to save message to database: {e}")

    except Exception as e:
        loguru.logger.error(f"Failed to handle message: {e}")
