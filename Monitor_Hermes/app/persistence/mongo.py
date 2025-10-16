from pymongo import AsyncMongoClient
from app.settings import settings
from datetime import datetime, timezone
from app.persistence.models import MessageIn
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
