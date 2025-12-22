from typing import List
from app.persistence.models import MessageDB


async def last_five_messages(db, dev_eui: str) -> List[MessageDB]:
    cursor = db.messages.find({"dev_eui": dev_eui}).sort("timestamp", -1).limit(5)
    messages = []
    async for doc in cursor:
        messages.append(MessageDB(**doc))
    return messages
