# Here we define the WebSocket routes for the application.
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.ws.manager import ConnectionManager

router = APIRouter()
manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(f"Message text was: {data}", websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast("A user has disconnected")
