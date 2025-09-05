# Manager in charge of:
# - Saving active connections in a list
# - Allowing to connect and disconnect
# - Broadcast messages to all active connections
import loguru
from typing import List, Dict
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.tenants: Dict[str, List[WebSocket]] = {}
        self.global_connections: List[WebSocket] = []
        self.super_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket, info: dict):
        await websocket.accept()
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
            tenant_id = info.get("tenant_id")
            loguru.logger.info(
                f"User connection established: \n User: {str(info.get('username'))} \n Tenant: {str(tenant_id)}"
            )
            if tenant_id not in self.tenants:
                self.tenants[tenant_id] = []
            self.tenants[tenant_id].append(websocket)

    def disconnect(self, websocket: WebSocket, info: dict):
        if info.get("is_global"):
            loguru.logger.info("Global connection closed")
            self.global_connections.remove(websocket)
        elif info.get("is_superuser"):
            loguru.logger.info("Superuser connection closed")
            self.super_connections.remove(websocket)
        else:
            tenant_id = info.get("tenant_id")
            loguru.logger.info(f"Tenant {tenant_id} connection closed")
            if tenant_id in self.tenants:
                self.tenants[tenant_id].remove(websocket)
                if not self.tenants[tenant_id]:
                    del self.tenants[tenant_id]

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str, tenant_id: str):
        for connection in self.tenants.get(tenant_id, []):
            await connection.send_text(message)
        for connection in self.super_connections + self.global_connections:
            await connection.send_text(message)
