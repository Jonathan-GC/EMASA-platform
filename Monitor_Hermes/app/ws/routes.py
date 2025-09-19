# Here we define the WebSocket routes for the application.
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

# from app.ws.manager import ConnectionManager
from app.ws.manager import manager
from app.auth.jwt import verify_jwt
import loguru

router = APIRouter()
# manager = ConnectionManager()


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
