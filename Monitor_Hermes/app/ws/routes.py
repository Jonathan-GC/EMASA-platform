# Here we define the WebSocket routes for the application.
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict

# from app.ws.manager import ConnectionManager
from app.ws.manager import manager
from app.auth.jwt import verify_jwt
import loguru
from cryptography.fernet import Fernet, InvalidToken
from app.settings import settings

from typing import List

router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self.tenants: Dict[str, List[WebSocket]] = {}
        self.global_connections: List[WebSocket] = []
        self.super_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket, info: dict):
        # removed: await websocket.accept()
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

    # Accept only after token validated
    await websocket.accept()
    await manager.connect(websocket, info)

    # If client requested to subscribe on connect: ?device=<dev_eui>
    initial_device = websocket.query_params.get("device")
    # try to decrypt device if WS_SECRET is set (client may send encrypted dev_eui)
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
            # expect either plain text or JSON control messages
            raw = await websocket.receive_text()
            # try to parse a JSON control message
            action = None
            device = None
            try:
                import json

                payload = json.loads(raw)
                action = payload.get("action")
                device = payload.get("device")
                # if device provided in JSON and secret exists try to decrypt
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
                # not JSON: ignore control and treat as broadcast from tenant
                pass

            if action in ("subscribe", "sub") and device:
                await manager.subscribe_device(websocket, device)
                continue
            if action in ("unsubscribe", "unsub") and device:
                manager.unsubscribe_device(websocket, device)
                continue

            # fallback: broadcast message to tenant channels
            tenant_id = info.get("tenant_id")
            if tenant_id:
                await manager.broadcast({"text": raw}, tenant_id)
    except WebSocketDisconnect:
        # cleanup: disconnect and remove any device subscription requested on connect
        if initial_device:
            manager.unsubscribe_device(websocket, initial_device)
        manager.disconnect(websocket, info)
