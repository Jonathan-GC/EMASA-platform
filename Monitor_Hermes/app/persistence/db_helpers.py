from typing import List, Optional, Dict, Any
from app.persistence.models import MessageDB

from datetime import datetime


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


async def aggregations(
    db,
    dev_eui: str,
    measurement_type: str,
    start: datetime,
    end: datetime,
    steps: int,
    channel: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Generates aggregated time series data (min, max, avg) for a given range and resolution.
    Optimized for MongoDB Time Series collections.
    """
    # Validate steps
    if steps < 1:
        steps = 1

    # Ensure the time range is valid (start should be earlier than or equal to end)
    if end < start:
        start, end = end, start

    # Calculate interval in milliseconds
    duration_ms = (end - start).total_seconds() * 1000
    interval_ms = max(1, int(duration_ms / steps))

    # Build Match Stage
    match_stage = {
        "meta.d": dev_eui,
        "meta.m": measurement_type,
        "ts": {"$gte": start, "$lte": end},
    }

    # Filter by channel if provided
    if channel:
        match_stage["meta.c"] = channel

    pipeline = [
        {"$match": match_stage},
        {
            "$group": {
                "_id": {
                    "channel": "$meta.c",
                    "time": {
                        "$toDate": {
                            "$subtract": [
                                {"$toLong": "$ts"},
                                {"$mod": [{"$toLong": "$ts"}, interval_ms]},
                            ]
                        }
                    },
                },
                "avg": {"$avg": "$val"},
                "min": {"$min": "$val"},
                "max": {"$max": "$val"},
            }
        },
        {"$sort": {"_id.time": 1}},
        {
            "$project": {
                "_id": 0,
                "timestamp": "$_id.time",
                "channel": "$_id.channel",
                "avg": {"$round": ["$avg", 2]},
                "min": "$min",
                "max": "$max",
            }
        },
    ]

    results = []
    cursor = await db.measurements_history.aggregate(pipeline)
    async for doc in cursor:
        results.append(doc)

    return results


async def get_historic_from_date_range(
    db,
    dev_eui: str,
    measurement_type: str,
    start: datetime,
    end: datetime,
    channel: Optional[str] = None,
) -> List[MessageDB]:
    """
    Retrieves historical measurement data for a specified device and measurement type within a given date range.
    It uses messages collection to fetch the data, since it needs to be the raw data for detailed analysis.

    Parameters:
    - db: Database connection
    - dev_eui: Device unique identifier
    - measurement_type: Type of measurement (e.g., voltage, current)
    - start: Start datetime for the range
    - end: End datetime for the range
    - channel: Optional channel filter
    """
    match_stage = {
        "dev_eui": dev_eui,
        "measurement_type": measurement_type,
        "timestamp": {"$gte": start, "$lte": end},
    }

    if channel:
        match_stage["channel"] = channel

    cursor = db.messages.find(match_stage).sort("timestamp", 1)
    messages = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        messages.append(MessageDB(**doc))
    return messages
