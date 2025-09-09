from app.persistence.models import MessageIn
from app.persistence.mongo import save_message
from app.ws.manager import manager
import asyncio
import loguru
import json


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
        future = asyncio.run_coroutine_threadsafe(save_message(db, message), loop)
        try:
            future.result()  # Wait for the result to ensure completion
            loguru.logger.info(
                f"Message saved to database for device {message.device_id} in tenant {message.tenant_id}"
            )
        except Exception as e:
            loguru.logger.error(f"Failed to save message to database: {e}")

        broadcast_future = asyncio.run_coroutine_threadsafe(
            manager.broadcast(message.model_dump(), message.tenant_id),
            loop,
        )
        try:
            broadcast_future.result()
        except Exception as e:
            loguru.logger.error(f"Failed to broadcast message: {e}")

    except Exception as e:
        loguru.logger.error(f"Failed to handle message: {e}")
