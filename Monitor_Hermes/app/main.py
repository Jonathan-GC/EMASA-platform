# App starting point
from fastapi import FastAPI, Depends
from app.ws.routes import router as ws_router
from contextlib import asynccontextmanager
from app.persistence.mongo import (
    connect_to_mongo,
    close_mongo_connection,
    get_db,
    save_message,
)
from app.redis.redis import connect_to_redis, close_redis_connection
from app.workers.redis_worker import process_messages
from app.persistence.models import MessageIn
from app.mqtt.client import start_mqtt
import loguru
import asyncio
from app.ws.manager import manager
from app.auth.deps import verify_service_api_key
from app.clients.atlas_client import atlas_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    await connect_to_redis()
    loop = asyncio.get_event_loop()
    db = await get_db()
    loop.create_task(process_messages(db))

    start_mqtt(db, loop)
    yield
    await close_mongo_connection()
    await close_redis_connection()


app = FastAPI(lifespan=lifespan)
app.include_router(ws_router)


@app.post("/messages")
async def create_message(message: MessageIn, db=Depends(get_db)):
    insert_id = await save_message(db, message)
    return {"insert_id": insert_id}


@app.post("/notify")
async def notify_user(
    user_id: str,
    title: str,
    message: str,
    type: str = "info",
    _: bool = Depends(verify_service_api_key),
):
    """
    Endpoint para que Atlas notifique a usuarios vía WebSocket.
    Requiere autenticación mediante X-API-Key header.
    """
    loguru.logger.debug(f"Notificando al usuario {user_id}: {message}")
    payload = {
        "channel": "notifications",
        "title": title,
        "message": message,
        "type": type,
    }
    try:
        await manager.send_to_user(user_id, payload)
        return {"status": "success", "sent": True}
    except Exception:
        loguru.logger.exception(f"Failed to notify user {user_id} via websocket")
        return {"status": "error", "sent": False}


@app.get("/devices/{device_id}/metadata")
async def get_device_metadata(device_id: str, _: bool = Depends(verify_service_api_key)):
    """
    Obtiene metadata de un dispositivo desde Atlas.
    Endpoint protegido con API Key.
    """
    metadata = await atlas_client.get_device_metadata(device_id)
    if metadata:
        return metadata
    return {"error": "Device not found or Atlas unavailable"}, 404


@app.post("/devices/{device_id}/notify-owner")
async def notify_device_owner(
    device_id: str,
    title: str,
    message: str,
    type: str = "info",
    _: bool = Depends(verify_service_api_key),
):
    """
    Notifica al owner de un dispositivo.
    Obtiene el owner_id desde Atlas y envía la notificación vía WebSocket.
    """
    # Obtener metadata del device desde Atlas
    device_metadata = await atlas_client.get_device_metadata(device_id)
    
    if not device_metadata:
        return {"status": "error", "message": "Device not found", "sent": False}
    
    owner_id = device_metadata.get("owner_id")
    if not owner_id:
        return {"status": "error", "message": "Device has no owner", "sent": False}
    
    # Enviar notificación al owner
    payload = {
        "channel": "notifications",
        "title": title,
        "message": message,
        "type": type,
        "device_id": device_id,
        "device_name": device_metadata.get("name", device_id),
    }
    
    try:
        await manager.send_to_user(str(owner_id), payload)
        return {"status": "success", "sent": True, "owner_id": owner_id}
    except Exception as e:
        loguru.logger.exception(f"Failed to notify owner {owner_id} of device {device_id}")
        return {"status": "error", "sent": False, "error": str(e)}
