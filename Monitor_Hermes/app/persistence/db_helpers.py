from typing import List
from app.persistence.models import MessageDB


async def get_last_messages(db, dev_eui: str, limit: int = 5) -> List[MessageDB]:
    if limit <= 0:
        limit = 5
    elif limit > 50:
        limit = 50
    cursor = db.messages.find({"dev_eui": dev_eui}).sort("timestamp", -1).limit(limit)
    messages = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        messages.append(MessageDB(**doc))
    return messages
