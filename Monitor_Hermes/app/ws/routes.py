# Here we define the WebSocket routes for the application.
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict

# from app.ws.manager import ConnectionManager
from app.ws.manager import manager
from app.auth.jwt import verify_jwt
import loguru

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

    try:
        while True:
            data = await websocket.receive_text()
            tenant_id = info.get("tenant_id")
            if tenant_id:
                await manager.broadcast(
                    f"Message from tenant {tenant_id}: {data}", tenant_id
                )
    except WebSocketDisconnect:
        manager.disconnect(websocket, info)
