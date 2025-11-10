"""
Worker de prueba para enviar notificaciones periódicas a Atlas.
Envía una notificación cada 10 segundos aproximadamente.
"""

import asyncio
import loguru
from app.clients.atlas import atlas_client


async def send_test_notification():
    """
    Envía una notificación de prueba a Atlas.
    """
    payload = {
        "title": "This is a test notification",
        "message": "This is a test notification, trying to communicate with atlas",
        "type": "info",
        "user": 1,
    }

    try:
        response = await atlas_client.post(
            "/api/v1/support/notification/alert/", json=payload
        )
        loguru.logger.info(
            f"✅ Test notification sent successfully. Status: {response.status_code}"
        )
        return response
    except Exception as e:
        loguru.logger.error(f"❌ Failed to send test notification: {e}")
        return None


async def test_notification_loop():
    """
    Loop infinito que envía notificaciones de prueba cada 10 segundos.
    """
    loguru.logger.info("🚀 Starting test notification worker...")

    while True:
        try:
            await send_test_notification()
            await asyncio.sleep(10)  # Esperar 10 segundos
        except Exception as e:
            loguru.logger.error(f"Error in test notification loop: {e}")
            await asyncio.sleep(10)  # Esperar antes de reintentar
