# App starting point
from typing import Any
from fastapi import FastAPI, Depends
from app.ws.routes import router as ws_router
from contextlib import asynccontextmanager
from app.persistence.mongo import (
    connect_to_mongo,
    close_mongo_connection,
    get_db,
    save_message,
)
from app.persistence.db_helpers import get_last_messages, aggregations
from app.redis.redis import connect_to_redis, close_redis_connection
from app.workers.redis_worker import process_messages
from app.workers.alert_retry_worker import retry_pending_alerts
from app.persistence.models import MessageIn, DeviceUserMapping
from app.persistence.device_mapping import update_device_user_mapping_cache
from app.validation.measurement_cache import force_refresh_measurement_configs
from app.mqtt.client import start_mqtt
import loguru
import asyncio
from datetime import datetime
from typing import Optional
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


@app.get("/messages/last")
async def get_last_messages_endpoint(
    dev_eui: str,
    limit: int = 5,
    db: Any = Depends(get_db),
    _: bool = Depends(verify_service_api_key),
):
    loguru.logger.debug(f"Fetching last {limit} messages for {dev_eui}")
    return await get_last_messages(db, dev_eui, limit)


@app.get("/measurements/history")
async def get_measurements_history(
    dev_eui: str,
    measurement_type: str,
    start: datetime,
    end: datetime,
    steps: int = 100,
    channel: Optional[str] = None,
    db: Any = Depends(get_db),
    _: bool = Depends(verify_service_api_key),
):
    """
    Get aggregated historical measurements for a device.

    - **dev_eui**: Device EUI
    - **measurement_type**: Type of measurement (e.g., "voltage", "current")
    - **start**: Start datetime (ISO 8601)
    - **end**: End datetime (ISO 8601)
    - **steps**: Number of data points to return (resolution)
    - **channel**: Optional channel filter (e.g., "ch1")
    """
    loguru.logger.debug(
        f"Fetching history for {dev_eui} ({measurement_type}) from {start} to {end}"
    )
    return await aggregations(db, dev_eui, measurement_type, start, end, steps, channel)


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


@app.post("/internal/mappings/device-user")
async def update_device_user_mapping_endpoint(
    mapping: DeviceUserMapping,
    db=Depends(get_db),
    _: bool = Depends(verify_service_api_key),
):
    """
    Update device-user mapping in cache and database.

    This endpoint is called by external services (e.g. Atlas) when
    a device is assigned or unassigned from a user.
    Requires SERVICE_API_KEY authentication.
    """
    try:
        await update_device_user_mapping_cache(db, mapping)
        return {
            "status": "success",
            "message": f"Mapping updated for {mapping.dev_eui}",
        }
    except Exception as e:
        loguru.logger.exception(f"Failed to update mapping for {mapping.dev_eui}: {e}")
        return {"status": "error", "message": str(e)}


@app.post("/internal/measurements/refresh")
async def refresh_measurements_endpoint(
    dev_eui: str,
    db=Depends(get_db),
    _: bool = Depends(verify_service_api_key),
):
    """
    Force refresh measurement configurations for a device.

    This endpoint is called by external services (e.g. Atlas) when
    measurement limits or configurations are updated.
    Requires SERVICE_API_KEY authentication.
    """
    success = await force_refresh_measurement_configs(dev_eui, db)

    if success:
        return {"status": "success", "message": f"Measurements refreshed for {dev_eui}"}
    else:
        return {
            "status": "error",
            "message": f"Failed to refresh measurements for {dev_eui}",
        }
