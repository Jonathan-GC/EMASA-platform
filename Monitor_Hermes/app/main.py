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
from app.workers.alert_retry_worker import retry_pending_alerts
from app.persistence.models import MessageIn
from app.mqtt.client import start_mqtt
import loguru
import asyncio
from app.ws.helpers import notify_user
from app.auth.deps import verify_service_api_key


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    await connect_to_redis()
    loop = asyncio.get_event_loop()
    db = await get_db()
    loop.create_task(process_messages(db))
    loop.create_task(retry_pending_alerts())

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
async def notify_user_endpoint(
    user_id: str,
    title: str,
    message: str,
    type: str = "info",
    _: bool = Depends(verify_service_api_key),
):
    """
    Send a notification to a user via WebSocket.

    This endpoint allows external services to send notifications to users.
    Requires SERVICE_API_KEY authentication via X-API-Key header.
    """
    loguru.logger.debug(f"Notifying user {user_id}: {message}")

    success = await notify_user(user_id, title, message, type)

    if success:
        return {"status": "success", "sent": True}
    else:
        return {"status": "error", "sent": False}
