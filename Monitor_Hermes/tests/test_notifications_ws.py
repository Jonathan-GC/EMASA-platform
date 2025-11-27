"""
Test script for WebSocket notifications channel.

Usage:
    python tests/test_notifications_ws.py
"""

import websockets
import asyncio
import loguru
import json

# ⚠️ CAMBIAR ESTE TOKEN POR UNO VÁLIDO DE TU SISTEMA
ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzU3MzYzNDM1LCJpYXQiOjE3NTczNTk4MzUsImp0aSI6IjRjY2YxZjFhNTY3MzQ3YTRiMDM0OTg3MTk4YzY3YmQ0IiwidXNlcl9pZCI6MSwidXNlcm5hbWUiOiJ3ZWVkbyIsImlzX2dsb2JhbCI6ZmFsc2UsImNzX3RlbmFudF9pZCI6bnVsbCwiaXNfc3VwZXJ1c2VyIjp0cnVlfQ.Q4RuVfRQrnIVxOWRitasfcSC4FQz2YsuJnJYR7E80-U"

URL = f"ws://localhost:5000/ws/notifications?token={ACCESS_TOKEN}"


async def test_notifications():
    """Test WebSocket notifications connection and message exchange."""
    try:
        async with websockets.connect(URL) as websocket:
            loguru.logger.success("✉️ Conectado al canal de notificaciones")

            # Enviar un ping inicial
            await websocket.send(json.dumps({"action": "ping"}))
            loguru.logger.debug("📤 Ping enviado")

            # Contador de mensajes recibidos
            message_count = 0

            while True:
                msg = await websocket.recv()
                data = json.loads(msg)
                message_count += 1

                loguru.logger.debug(f"📬 Mensaje #{message_count} recibido:")
                loguru.logger.debug(f"   {json.dumps(data, indent=2)}")

                # Si es una notificación, enviar ACK
                if data.get("channel") == "notifications":
                    notification_type = data.get("type", "info")
                    title = data.get("title", "Sin título")
                    message = data.get("message", "Sin mensaje")

                    # Simular procesamiento de notificación
                    emoji = {
                        "info": "ℹ️",
                        "success": "✅",
                        "warning": "⚠️",
                        "error": "❌",
                    }.get(notification_type, "📧")

                    loguru.logger.success(f"{emoji} NOTIFICACIÓN: {title}")
                    loguru.logger.debug(f"   📝 {message}")

                    # Enviar ACK
                    await websocket.send(
                        json.dumps(
                            {
                                "action": "ack",
                                "notification_id": data.get(
                                    "id", f"msg-{message_count}"
                                ),
                            }
                        )
                    )
                    loguru.logger.debug("✓ ACK enviado")

                # Si es un pong, registrarlo
                elif data.get("action") == "pong":
                    loguru.logger.debug("🏓 Pong recibido")

    except websockets.exceptions.ConnectionClosed as e:
        loguru.logger.warning(f"🔌 Conexión cerrada: {e}")
    except Exception as e:
        loguru.logger.error(f"❌ Error: {e}")
        raise


async def test_with_heartbeat():
    """Test notifications with periodic heartbeat."""
    try:
        async with websockets.connect(URL) as websocket:
            loguru.logger.success(
                "✉️ Conectado al canal de notificaciones (con heartbeat)"
            )

            async def send_heartbeat():
                """Send periodic heartbeat every 30 seconds."""
                while True:
                    await asyncio.sleep(30)
                    try:
                        await websocket.send(json.dumps({"action": "ping"}))
                        loguru.logger.debug("💓 Heartbeat enviado")
                    except Exception as e:
                        loguru.logger.error(f"Error enviando heartbeat: {e}")
                        break

            # Iniciar heartbeat en background
            heartbeat_task = asyncio.create_task(send_heartbeat())

            try:
                while True:
                    msg = await websocket.recv()
                    data = json.loads(msg)

                    if data.get("channel") == "notifications":
                        notification_type = data.get("type", "info")
                        emoji = {
                            "info": "ℹ️",
                            "success": "✅",
                            "warning": "⚠️",
                            "error": "❌",
                        }.get(notification_type, "📧")

                        loguru.logger.success(
                            f"{emoji} {data.get('title')}: {data.get('message')}"
                        )
            finally:
                heartbeat_task.cancel()

    except Exception as e:
        loguru.logger.error(f"❌ Error: {e}")
        raise


async def test_multiple_connections():
    """Test multiple simultaneous connections (simulating multiple devices)."""

    async def client_connection(client_id):
        try:
            async with websockets.connect(URL) as websocket:
                loguru.logger.success(f"✉️ Cliente {client_id} conectado")

                while True:
                    msg = await websocket.recv()
                    data = json.loads(msg)

                    if data.get("channel") == "notifications":
                        loguru.logger.debug(
                            f"📬 Cliente {client_id} recibió: {data.get('title')}"
                        )
        except Exception as e:
            loguru.logger.error(f"❌ Cliente {client_id} error: {e}")

    # Crear 3 conexiones simultáneas (simulando 3 dispositivos del mismo usuario)
    await asyncio.gather(
        client_connection("A (Desktop)"),
        client_connection("B (Mobile)"),
        client_connection("C (Tablet)"),
    )


if __name__ == "__main__":
    loguru.logger.debug("🚀 Iniciando test de WebSocket de notificaciones")
    loguru.logger.debug(f"📡 URL: {URL}")
    loguru.logger.debug("=" * 60)

    # Descomentar el test que quieras ejecutar:

    # Test básico
    asyncio.run(test_notifications())

    # Test con heartbeat
    # asyncio.run(test_with_heartbeat())

    # Test con múltiples conexiones
    # asyncio.run(test_multiple_connections())
