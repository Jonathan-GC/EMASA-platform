"""
Script to test sending notifications via POST /notify endpoint.

This simulates another API sending notifications to Monitor_Hermes.

Usage:
    python tests/test_send_notification.py
"""

import requests
import time
import loguru

HERMES_API_URL = "http://localhost:5000"


def send_notification(user_id: str, title: str, message: str, type: str = "info"):
    """
    Send a notification to a specific user via WebSocket.

    Args:
        user_id: ID of the user to notify
        title: Notification title
        message: Notification message
        type: Type of notification (info, success, warning, error)

    Returns:
        dict: Response from the API
    """
    try:
        payload = {
            "user_id": user_id,
            "title": title,
            "message": message,
            "type": type,
        }

        loguru.logger.debug(f"📤 Enviando notificación a usuario {user_id}")
        loguru.logger.debug(f"   Payload: {payload}")

        response = requests.post(f"{HERMES_API_URL}/notify", json=payload)
        response.raise_for_status()

        result = response.json()
        loguru.logger.success(f"✅ Respuesta: {result}")

        return result

    except requests.RequestException as e:
        loguru.logger.error(f"❌ Failed to send notification via WebSocket: {e}")
        return {"status": "error", "sent": False, "error": str(e)}


def test_notifications_sequence():
    """Send a sequence of test notifications."""

    # ⚠️ CAMBIAR POR EL USER_ID CORRECTO DE TU SISTEMA
    TEST_USER_ID = "1"

    notifications = [
        {
            "title": "Bienvenido",
            "message": "Sistema de notificaciones funcionando correctamente",
            "type": "success",
        },
        {
            "title": "Alerta de sensor",
            "message": "El sensor ABC-123 ha superado el umbral de temperatura",
            "type": "warning",
        },
        {
            "title": "Error de conexión",
            "message": "No se pudo conectar con el dispositivo XYZ-789",
            "type": "error",
        },
        {
            "title": "Información",
            "message": "Mantenimiento programado para mañana a las 03:00 AM",
            "type": "info",
        },
        {
            "title": "Actualización completada",
            "message": "Todos los dispositivos han sido actualizados exitosamente",
            "type": "success",
        },
    ]

    loguru.logger.debug(f"🚀 Enviando {len(notifications)} notificaciones de prueba")
    loguru.logger.debug(f"👤 Usuario destino: {TEST_USER_ID}")
    loguru.logger.debug("=" * 60)

    for i, notif in enumerate(notifications, 1):
        loguru.logger.debug(f"\n📨 Notificación {i}/{len(notifications)}")
        result = send_notification(
            user_id=TEST_USER_ID,
            title=notif["title"],
            message=notif["message"],
            type=notif["type"],
        )

        if result.get("sent"):
            loguru.logger.success(f"   ✓ Entregada correctamente")
        else:
            loguru.logger.warning(f"   ⚠ No se pudo entregar (usuario no conectado)")

        # Esperar un poco entre notificaciones para que sea más claro en el cliente
        time.sleep(2)

    loguru.logger.debug("\n" + "=" * 60)
    loguru.logger.success("✅ Secuencia de prueba completada")


def test_notification_to_offline_user():
    """Test sending notification to a user that is not connected."""

    # Usuario que probablemente no existe o no está conectado
    OFFLINE_USER_ID = "99999"

    loguru.logger.debug(
        f"🧪 Probando notificación a usuario offline ({OFFLINE_USER_ID})"
    )

    result = send_notification(
        user_id=OFFLINE_USER_ID,
        title="Test offline",
        message="Esta notificación no debería ser entregada",
        type="info",
    )

    if not result.get("sent"):
        loguru.logger.success(
            "✅ Comportamiento correcto: notificación no entregada (usuario offline)"
        )
    else:
        loguru.logger.warning(
            "⚠️ Inesperado: la notificación fue marcada como entregada"
        )


if __name__ == "__main__":
    loguru.logger.debug("🔔 Test de envío de notificaciones")
    loguru.logger.debug(f"🌐 API URL: {HERMES_API_URL}")
    loguru.logger.debug("=" * 60)

    # Primero asegúrate de tener un cliente WebSocket conectado
    # ejecutando: python tests/test_notifications_ws.py

    input(
        "\n⚠️  Asegúrate de tener un cliente WebSocket conectado primero.\n"
        "   Ejecuta en otra terminal: python tests/test_notifications_ws.py\n"
        "   Presiona ENTER cuando estés listo..."
    )

    print()

    # Ejecutar secuencia de prueba
    test_notifications_sequence()

    print("\n" + "=" * 60)
    input("Presiona ENTER para probar notificación a usuario offline...")
    print()

    # Probar con usuario offline
    test_notification_to_offline_user()
