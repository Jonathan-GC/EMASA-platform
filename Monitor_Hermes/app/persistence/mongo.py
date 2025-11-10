from pymongo import AsyncMongoClient
from app.settings import settings
from datetime import datetime, timezone
from app.persistence.models import MessageIn, DeviceMeasurements
import loguru

client: AsyncMongoClient = None


async def get_db():
    return client[settings.MONGO_DB]


async def connect_to_mongo():
    global client
    client = AsyncMongoClient(settings.MONGO_URI)
    loguru.logger.debug("Connected to MongoDB")


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


async def save_device_measurements(db, measurements: DeviceMeasurements):
    """
    Save or update device measurements in MongoDB.
    If a document with the same dev_eui exists, it will be updated.
    Otherwise, a new document will be created.
    """
    doc = measurements.model_dump()
    now = datetime.now(timezone.utc)

    # Try to update existing document
    result = await db.device_measurements.update_one(
        {"dev_eui": measurements.dev_eui},
        {"$set": {**doc, "updated_at": now}, "$setOnInsert": {"created_at": now}},
        upsert=True,
    )

    return str(result.upserted_id) if result.upserted_id else measurements.dev_eui


async def get_device_measurements(db, dev_eui: str):
    """
    Get device measurements by dev_eui.
    """
    doc = await db.device_measurements.find_one({"dev_eui": dev_eui})
    return doc
