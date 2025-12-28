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
    if steps < 1:
        steps = 1

    # Calculate interval in milliseconds
    duration_ms = (end - start).total_seconds() * 1000
    interval_ms = max(1, duration_ms / steps)

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
                    # Mathematical bucketing: floor(ts / interval) * interval
                    # This creates regular time buckets based on the requested steps
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
                "avg": {"$round": ["$avg", 2]},  # Round for cleaner JSON
                "min": "$min",
                "max": "$max",
            }
        },
    ]

    results = []
    async for doc in db.measurements_history.aggregate(pipeline):
        results.append(doc)

    return results
