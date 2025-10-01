# Manager in charge of:
# - Saving active connections in a list
# - Allowing to connect and disconnect
# - Broadcast messages to all active connections
import loguru
from typing import List, Dict, Set
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.tenants: Dict[str, List[WebSocket]] = {}
        self.global_connections: List[WebSocket] = []
        self.super_connections: List[WebSocket] = []
        self.device_subs: Dict[str, Set[WebSocket]] = {}

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
        try:
            for dev, conns in list(self.device_subs.items()):
                if websocket in conns:
                    conns.discard(websocket)
                    if not conns:
                        del self.device_subs[dev]
        except Exception:
            loguru.logger.exception("Error cleaning device subscriptions on disconnect")

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
                if connection in self.super_connections:
                    self.super_connections.remove(connection)
                elif connection in self.global_connections:
                    self.global_connections.remove(connection)

    async def subscribe_device(self, websocket: WebSocket, dev_eui: str):
        """Subscribe a websocket to a device EUI.

        Uses a set to avoid duplicates and speed up removals.
        """
        if not dev_eui:
            return
        key = str(dev_eui)
        if key not in self.device_subs:
            self.device_subs[key] = set()
        self.device_subs[key].add(websocket)
        loguru.logger.info(f"WebSocket subscribed to device {key}")

    def unsubscribe_device(self, websocket: WebSocket, dev_eui: str):
        if not dev_eui:
            return
        key = str(dev_eui)
        if key in self.device_subs and websocket in self.device_subs[key]:
            self.device_subs[key].discard(websocket)
            if not self.device_subs[key]:
                del self.device_subs[key]
            loguru.logger.info(f"WebSocket unsubscribed from device {key}")

    async def broadcast_to_device(self, message: dict, dev_eui: str):
        """Send message dict to all websockets subscribed to dev_eui.

        Cleans up dead connections on error.
        """
        if not dev_eui:
            return
        key = str(dev_eui)
        conns = list(self.device_subs.get(key, set()))
        for conn in conns:
            try:
                await conn.send_json(message)
            except Exception:
                if key in self.device_subs and conn in self.device_subs[key]:
                    self.device_subs[key].discard(conn)
                loguru.logger.exception(
                    f"Failed to send message to subscriber of {key}"
                )
        if key in self.device_subs and not self.device_subs[key]:
            del self.device_subs[key]


manager = ConnectionManager()
