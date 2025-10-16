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
async def notify_user(user_id: str, title: str, message: str, type: str = "info"):
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
