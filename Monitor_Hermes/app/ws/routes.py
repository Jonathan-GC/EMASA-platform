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


class ConnectionManager:
    def __init__(self):
        self.tenants: Dict[str, List[WebSocket]] = {}
        self.global_connections: List[WebSocket] = []
        self.super_connections: List[WebSocket] = []
        self.device_subscriptions: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, info: dict):
        if info.get("is_global"):
            loguru.logger.info(
                f"Global connection established: \n User: {str(info.get('username'))} \n Tenant: {str(info.get('tenant_id'))}"
            )
            self.global_connections.append(websocket)
        elif info.get("is_superuser"):
            loguru.logger.info(
                f"Superuser connection established: \n User: {str(info.get('username'))} \n Superuser: {str(info.get('is_superuser'))}"
            )
            self.super_connections.append(websocket)
        else:
            tenant_id = str(info.get("tenant_id"))
            loguru.logger.info(
                f"User connection established: \n User: {str(info.get('username'))} \n Tenant: {str(tenant_id)}"
            )
            if tenant_id not in self.tenants:
                self.tenants[tenant_id] = []
            self.tenants[tenant_id].append(websocket)

    async def disconnect(self, websocket: WebSocket, info: dict):
        if info.get("is_global"):
            self.global_connections.remove(websocket)
        elif info.get("is_superuser"):
            self.super_connections.remove(websocket)
        else:
            tenant_id = str(info.get("tenant_id"))
            if tenant_id in self.tenants:
                self.tenants[tenant_id].remove(websocket)

    async def subscribe_device(self, websocket: WebSocket, dev_eui: str):
        if dev_eui not in self.device_subscriptions:
            self.device_subscriptions[dev_eui] = []
        self.device_subscriptions[dev_eui].append(websocket)

    def unsubscribe_device(self, websocket: WebSocket, dev_eui: str):
        if dev_eui in self.device_subscriptions:
            self.device_subscriptions[dev_eui].remove(websocket)
            if not self.device_subscriptions[dev_eui]:
                del self.device_subscriptions[dev_eui]

    async def broadcast_to_device(self, message: dict, dev_eui: str):
        if dev_eui in self.device_subscriptions:
            for connection in list(self.device_subscriptions[dev_eui]):
                try:
                    await connection.send_json(message)
                except Exception:
                    self.device_subscriptions[dev_eui].remove(connection)


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

    # desencriptar dev_eui
    dev_eui = None
    if settings.WS_SECRET:
        try:
            key = settings.WS_SECRET.encode("utf-8")
            f = Fernet(key)
            dev_eui = f.decrypt(enc_dev_eui.encode("utf-8")).decode("utf-8")
        except Exception:
            await websocket.close(code=1008)
            return

    # validar que el usuario tiene acceso a ese dev_eui según tenant_id
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

    # Aceptar y subscribir al canal del device
    try:
        # Cuando la conexión llega por la ruta /ws/device/ queremos que solo
        # esté suscrita al device concreto, no como conexión global/superuser.
        info_for_device = dict(info)  # no mutamos el objeto original
        info_for_device["is_global"] = False
        info_for_device["is_superuser"] = False
        info_for_device["device_only"] = True  # <-- evita registro en tenant lists
        await manager.connect(websocket, info_for_device)
        await manager.subscribe_device(websocket, dev_eui)  # 🔑 SUSCRIPCIÓN AL DEVICE
        loguru.logger.info(f"Conectado al device {dev_eui} para tenant {tenant_id}")
    except Exception:
        loguru.logger.exception("Error registrando conexión")
        await websocket.close(code=500)
        return

    # Escuchar mensajes entrantes (si quieres recibir pings del cliente)
    try:
        while True:
            data = await websocket.receive_text()
            loguru.logger.debug(f"Mensaje entrante desde {dev_eui}: {data}")
            # aquí puedes responder si lo necesitas
    except WebSocketDisconnect:
        # use the same info_for_device that was used to register the connection
        manager.disconnect(
            websocket, info_for_device if "info_for_device" in locals() else info
        )
        manager.unsubscribe_device(websocket, dev_eui)
        loguru.logger.info(f"Conexión cerrada para device {dev_eui}")
