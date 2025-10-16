from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict

from app.ws.manager import manager
from app.auth.jwt import verify_jwt
import loguru
from cryptography.fernet import Fernet, InvalidToken
from app.settings import settings

from typing import List

from app.ws.filters import get_devEui_mapping

router = APIRouter()


@router.websocket("/ws/notifications")
async def websocket_notifications(websocket: WebSocket):
    """
    WebSocket dedicado EXCLUSIVAMENTE para notificaciones de usuario.

    El cliente se conecta a este endpoint para recibir notificaciones personales:
    - Alertas del sistema
    - Mensajes de la aplicación
    - Notificaciones de eventos importantes

    No recibe datos de devices ni de tenants, solo notificaciones enviadas
    específicamente al user_id del usuario autenticado.

    Uso desde el cliente:
        ws://host/ws/notifications?token=JWT_TOKEN

    Mensajes recibidos tienen el formato:
        {
            "channel": "notifications",
            "title": "Título de la notificación",
            "message": "Contenido del mensaje",
            "type": "info|warning|error|success"
        }
    """
    token = websocket.query_params.get("token")
    if not token:
        loguru.logger.warning("WebSocket notifications: No token provided")
        await websocket.close(code=1008)
        return

    try:
        info = verify_jwt(token)
    except Exception as e:
        loguru.logger.warning(f"WebSocket notifications: Invalid token - {e}")
        await websocket.close(code=1008)
        return

    await websocket.accept()

    # Crear info específico para conexión de notificaciones
    info_for_notifications = {
        "user_id": info.get("user_id"),
        "username": info.get("username"),
        "notification_only": True,  # Flag para identificar este tipo de conexión
        "tenant_id": info.get("tenant_id"),  # Mantener para logging
    }

    try:
        await manager.connect(websocket, info_for_notifications)
        loguru.logger.debug(
            f"✉️  User {info.get('username')} (ID: {info.get('user_id')}) connected to notifications channel"
        )
    except Exception:
        loguru.logger.exception("Error registering notifications connection")
        await websocket.close(code=500)
        return

    try:
        while True:
            # Mantener conexión abierta y permitir mensajes del cliente
            # (opcional: el cliente puede enviar heartbeat o ACKs)
            data = await websocket.receive_text()
            loguru.logger.debug(
                f"Notification channel received from {info.get('username')}: {data}"
            )

            # Opcional: permitir al cliente enviar comandos
            # Por ejemplo, marcar notificaciones como leídas, etc.
            try:
                import json

                payload = json.loads(data)
                action = payload.get("action")

                if action == "ping":
                    # Responder a heartbeat
                    await websocket.send_json({"action": "pong"})
                elif action == "ack":
                    # Cliente confirmó recepción de notificación
                    notification_id = payload.get("notification_id")
                    loguru.logger.debug(
                        f"User {info.get('username')} acknowledged notification {notification_id}"
                    )
                else:
                    loguru.logger.debug(
                        f"Unknown action in notifications channel: {action}"
                    )
            except Exception:
                # Si no es JSON o falla el parsing, ignorar
                pass

    except WebSocketDisconnect:
        manager.disconnect(websocket, info_for_notifications)
        loguru.logger.debug(
            f"✉️  User {info.get('username')} (ID: {info.get('user_id')}) disconnected from notifications channel"
        )


# currently unused, but could be useful later for tenant's dashboards
@router.websocket("/ws/tenant/{enc_tenant_id}")
async def websocket_tenant(websocket: WebSocket, enc_tenant_id: str):
    token = websocket.query_params.get("token")
    await websocket.accept()
    if not token:
        await websocket.close(code=1008)
        return

    try:
        info = verify_jwt(token)
    except Exception:
        await websocket.close(code=1008)
        return

    tenant_id = enc_tenant_id
    if settings.WS_SECRET:
        try:
            key = settings.WS_SECRET.encode("utf-8")
            f = Fernet(key)
            tenant_id = f.decrypt(enc_tenant_id.encode("utf-8")).decode("utf-8")
        except Exception:
            loguru.logger.exception("Could not decrypt tenant id in WS")
            await websocket.close(code=1008)
            return

    if not info.get("is_superuser") and str(info.get("tenant_id")) != str(tenant_id):
        loguru.logger.warning(
            f"User {info.get('username')} tried to access tenant channel {tenant_id} without permission"
        )
        await websocket.close(code=1008)
        return

    try:
        info_for_tenant = dict(info)
        info_for_tenant["is_global"] = False
        info_for_tenant["is_superuser"] = False
        info_for_tenant["device_only"] = False
        info_for_tenant["tenant_id"] = tenant_id
        await manager.connect(websocket, info_for_tenant)
        loguru.logger.debug(
            f"Connected to tenant channel {tenant_id} for user {info.get('username')}"
        )
    except Exception:
        loguru.logger.exception("Error registering tenant connection")
        await websocket.close(code=500)
        return

    try:
        while True:
            data = await websocket.receive_text()
            loguru.logger.debug(
                f"Incoming message on tenant channel {tenant_id}: {data}"
            )
    except WebSocketDisconnect:
        manager.disconnect(
            websocket, info_for_tenant if "info_for_tenant" in locals() else info
        )
        loguru.logger.debug(f"Connection closed for tenant {tenant_id}")


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008)
        return
    try:
        info = verify_jwt(token)
    except Exception:
        await websocket.close(code=1008)
        return

    await websocket.accept()
    await manager.connect(websocket, info)

    initial_device = websocket.query_params.get("device")
    if initial_device and settings.WS_SECRET:
        try:
            key = settings.WS_SECRET.encode("utf-8")
            f = Fernet(key)
            try:
                decrypted = f.decrypt(initial_device.encode("utf-8"))
                initial_device = decrypted.decode("utf-8")
            except InvalidToken:
                loguru.logger.debug(
                    "WS device query param could not be decrypted; using raw value"
                )
        except Exception:
            loguru.logger.exception(
                "Invalid WS_SECRET; cannot decrypt device parameter"
            )
    if initial_device:
        await manager.subscribe_device(websocket, initial_device)

    try:
        while True:
            raw = await websocket.receive_text()
            action = None
            device = None
            try:
                import json

                payload = json.loads(raw)
                action = payload.get("action")
                device = payload.get("device")
                if device and settings.WS_SECRET:
                    try:
                        key = settings.WS_SECRET.encode("utf-8")
                        f = Fernet(key)
                        try:
                            decrypted = f.decrypt(device.encode("utf-8"))
                            device = decrypted.decode("utf-8")
                        except InvalidToken:
                            loguru.logger.debug(
                                "WS JSON device could not be decrypted; using raw value"
                            )
                    except Exception:
                        loguru.logger.exception(
                            "Invalid WS_SECRET; cannot decrypt JSON device parameter"
                        )
            except Exception:
                pass

            if action in ("subscribe", "sub") and device:
                await manager.subscribe_device(websocket, device)
                continue
            if action in ("unsubscribe", "unsub") and device:
                manager.unsubscribe_device(websocket, device)
                continue

            tenant_id = info.get("tenant_id")
            if tenant_id:
                await manager.broadcast({"text": raw}, tenant_id)
    except WebSocketDisconnect:
        if initial_device:
            manager.unsubscribe_device(websocket, initial_device)
        manager.disconnect(websocket, info)


@router.websocket("/ws/device/{enc_dev_eui}")
async def websocket_device(websocket: WebSocket, enc_dev_eui: str):
    token = websocket.query_params.get("token")
    await websocket.accept()
    if not token:
        await websocket.close(code=1008)
        return

    try:
        info = verify_jwt(token)
    except Exception:
        await websocket.close(code=1008)
        return

    dev_eui = None
    if settings.WS_SECRET:
        try:
            key = settings.WS_SECRET.encode("utf-8")
            f = Fernet(key)
            dev_eui = f.decrypt(enc_dev_eui.encode("utf-8")).decode("utf-8")
        except Exception:
            await websocket.close(code=1008)
            return

    tenant_id = await get_devEui_mapping(dev_eui)
    if not tenant_id or str(tenant_id) != str(info.get("tenant_id")):
        loguru.logger.warning(
            f"User {info.get('username')} tried to access device {dev_eui} without permission"
        )
        if info.get("is_superuser"):
            loguru.logger.warning(
                f"User {info.get('username')} is a superuser and tried to access device {dev_eui} without permission"
            )
        else:
            await websocket.close(code=1008)
            return

    try:
        info_for_device = dict(info)
        info_for_device["is_global"] = False
        info_for_device["is_superuser"] = False
        info_for_device["device_only"] = True
        await manager.connect(websocket, info_for_device)
        await manager.subscribe_device(websocket, dev_eui)
        loguru.logger.debug(f"Connected to device {dev_eui} for tenant {tenant_id}")
    except Exception:
        loguru.logger.exception("Error registering connection")
        await websocket.close(code=500)
        return

    try:
        while True:
            data = await websocket.receive_text()
            loguru.logger.debug(f"Incoming message from {dev_eui}: {data}")
    except WebSocketDisconnect:
        manager.disconnect(
            websocket, info_for_device if "info_for_device" in locals() else info
        )
        manager.unsubscribe_device(websocket, dev_eui)
        loguru.logger.debug(f"Connection closed for device {dev_eui}")
