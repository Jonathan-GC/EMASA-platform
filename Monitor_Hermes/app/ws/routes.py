# Here we define the WebSocket routes for the application.
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.ws.manager import ConnectionManager
from app.auth.jwt import verify_jwt

router = APIRouter()
manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    try:
        info = verify_jwt(token)
    except Exception:
        await websocket.close(code=1008)
        return

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
