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
            tenant_id = str(info.get("tenant_id"))
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
            tenant_id = str(info.get("tenant_id"))
            loguru.logger.info(f"Tenant {tenant_id} connection closed")
            if tenant_id in self.tenants:
                self.tenants[tenant_id].remove(websocket)
                if not self.tenants[tenant_id]:
                    del self.tenants[tenant_id]

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: dict, tenant_id: str):
        tenant_key = str(tenant_id)
        # Specific tenant
        for connection in list(self.tenants.get(tenant_key, [])):
            try:
                await connection.send_json(message)
            except Exception:
                self.tenants[tenant_key].remove(connection)

        # Global and superuser
        for connection in list(self.super_connections + self.global_connections):
            try:
                await connection.send_json(message)
            except Exception:
                (
                    self.super_connections.remove(connection)
                    if connection in self.super_connections
                    else self.global_connections.remove(connection)
                )


manager = ConnectionManager()
