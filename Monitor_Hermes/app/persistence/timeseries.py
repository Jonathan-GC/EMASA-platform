from datetime import datetime
from typing import Dict, Any
import loguru
from pymongo.errors import BulkWriteError
from pymongo.database import Database


async def transform_and_insert_timeseries(db: Database, payload: Dict[str, Any]):
    """
    Transforms the raw payload into time series documents and inserts them into MongoDB.
    Uses insert_many with ordered=False for performance and fault tolerance.
    Ensures values are stored as floats for correct aggregation.
    """
    ts_docs = []

    dev_eui = payload.get("dev_eui")
    tenant_id = payload.get("tenant_id")

    if not dev_eui or not tenant_id:
        return

    base_meta = {
        "d": dev_eui,
        "t": tenant_id,
    }

    measurements = payload.get("payload", {}).get("measurements", {})

    for measure_type, channels in measurements.items():
        if not isinstance(channels, dict):
            continue

        for channel, points in channels.items():
            if not isinstance(points, list):
                continue

            meta = base_meta.copy()
            meta["m"] = measure_type
            meta["c"] = channel

            for point in points:
                if "time" in point and "value" in point:
                    try:
                        ts_str = point["time"].replace("Z", "+00:00")
                        ts = datetime.fromisoformat(ts_str)

                        val = float(point["value"])

                        ts_docs.append({"ts": ts, "meta": meta, "val": val})
                    except (ValueError, TypeError):
                        continue

    if not ts_docs:
        return

    try:
        await db.measurements_history.insert_many(ts_docs, ordered=False)
        loguru.logger.debug(f"Inserted {len(ts_docs)} time series points for {dev_eui}")
    except BulkWriteError as bwe:
        loguru.logger.warning(
            f"Partial insert error for {dev_eui}: {bwe.details['nInserted']} inserted, {len(bwe.details['writeErrors'])} failed."
        )
    except Exception as e:
        loguru.logger.error(f"Failed to insert historical batch for {dev_eui}: {e}")
