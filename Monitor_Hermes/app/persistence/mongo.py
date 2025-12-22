from pymongo import AsyncMongoClient, ASCENDING
from app.settings import settings
from datetime import datetime, timezone
from app.persistence.models import (
    MessageIn,
    DeviceMeasurementConfigs,
    MeasurementConfig,
    PendingAlert,
    DeviceUserMapping,
)
from typing import List, Optional
import loguru

client: AsyncMongoClient = None


async def get_db():
    return client[settings.MONGO_DB]


async def create_indexes():
    """Creates TTL indexes for data retention."""
    db = await get_db()
    # Create TTL index for messages (3 months = 90 days = 7,776,000 seconds)
    await db.messages.create_index(
        [("timestamp", ASCENDING)], expireAfterSeconds=7776000
    )
    loguru.logger.debug("TTL indexes created/verified")


async def connect_to_mongo():
    global client
    client = AsyncMongoClient(settings.MONGO_URI)
    loguru.logger.debug("Connected to MongoDB")
    await create_indexes()


async def close_mongo_connection():
    global client
    if client:
        client.close()
        loguru.logger.debug("Closed MongoDB connection")


async def save_message(db, message: MessageIn):
    doc = message.model_dump()
    doc["timestamp"] = datetime.now(timezone.utc)
    result = await db.messages.insert_one(doc)
    return str(result.inserted_id)


async def save_device_measurement_configs(
    db, dev_eui: str, configs: List[MeasurementConfig]
):
    now = datetime.now(timezone.utc)

    configs_dict = [config.model_dump() for config in configs]

    result = await db.device_measurement_configs.update_one(
        {"dev_eui": dev_eui},
        {
            "$set": {
                "configs": configs_dict,
                "last_updated": now,
            },
            "$setOnInsert": {
                "dev_eui": dev_eui,
                "last_fetched": now,
            },
        },
        upsert=True,
    )

    return str(result.upserted_id) if result.upserted_id else dev_eui


async def get_device_measurement_configs(
    db, dev_eui: str
) -> Optional[DeviceMeasurementConfigs]:
    doc = await db.device_measurement_configs.find_one({"dev_eui": dev_eui})
    if doc:
        return DeviceMeasurementConfigs(**doc)
    return None


async def save_pending_alert(db, alert: PendingAlert):
    doc = alert.model_dump()
    result = await db.pending_alerts.insert_one(doc)
    return str(result.inserted_id)


async def get_pending_alerts(db, limit: int = 100) -> List[dict]:
    cursor = db.pending_alerts.find(
        {"status": "pending", "retry_count": {"$lt": 3}}
    ).limit(limit)
    return await cursor.to_list(length=limit)


async def update_pending_alert_status(
    db,
    alert_id: str,
    status: str,
    retry_count: Optional[int] = None,
    error_message: Optional[str] = None,
):
    update_doc = {
        "status": status,
        "last_retry_at": datetime.now(timezone.utc),
    }

    if retry_count is not None:
        update_doc["retry_count"] = retry_count

    if error_message is not None:
        update_doc["error_message"] = error_message

    await db.pending_alerts.update_one({"_id": alert_id}, {"$set": update_doc})


async def save_device_user_mapping(db, mapping: DeviceUserMapping):
    doc = mapping.model_dump()
    now = datetime.now(timezone.utc)

    result = await db.device_user_mapping.update_one(
        {"dev_eui": mapping.dev_eui},
        {
            "$set": {**doc, "updated_at": now},
            "$setOnInsert": {"created_at": now},
        },
        upsert=True,
    )

    return str(result.upserted_id) if result.upserted_id else mapping.dev_eui


async def get_users_for_device(db, dev_eui: str) -> Optional[DeviceUserMapping]:
    doc = await db.device_user_mapping.find_one({"dev_eui": dev_eui})
    if doc:
        return DeviceUserMapping(**doc)
    return None
