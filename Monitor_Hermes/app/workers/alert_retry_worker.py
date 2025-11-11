"""
Alert retry worker.
Retries failed alerts to Atlas API in background.
"""

import asyncio
from datetime import datetime, timezone
import loguru

from app.clients.atlas import atlas_client
from app.persistence.mongo import (
    get_db,
    get_pending_alerts,
    update_pending_alert_status,
)
import httpx


async def retry_pending_alerts():
    """
    Background worker that retries pending alerts every 5 minutes.
    Max 3 retry attempts per alert.
    """
    loguru.logger.info("🔄 Alert retry worker started")

    while True:
        try:
            db = await get_db()
            pending = await get_pending_alerts(db, limit=100)

            if pending:
                loguru.logger.info(f"🔄 Retrying {len(pending)} pending alerts...")

            for alert_doc in pending:
                alert_id = alert_doc["_id"]
                dev_eui = alert_doc.get("dev_eui")
                alert_data = alert_doc.get("alert_data", {})
                retry_count = alert_doc.get("retry_count", 0)

                try:
                    response = await atlas_client.post(
                        "/api/v1/support/notification/alert/",
                        json=alert_data,
                        timeout=10.0,
                    )

                    await update_pending_alert_status(
                        db, alert_id, status="sent", retry_count=retry_count
                    )

                    loguru.logger.info(f"✅ Pending alert sent to Atlas: {dev_eui}")

                except (httpx.HTTPError, httpx.TimeoutException) as e:
                    new_retry_count = retry_count + 1
                    new_status = "failed" if new_retry_count >= 3 else "pending"

                    await update_pending_alert_status(
                        db,
                        alert_id,
                        status=new_status,
                        retry_count=new_retry_count,
                        error_message=str(e),
                    )

                    loguru.logger.warning(
                        f"⚠️ Retry {new_retry_count}/3 failed for {dev_eui}: {e}"
                    )

                except Exception as e:
                    loguru.logger.exception(
                        f"Unexpected error retrying alert {alert_id}: {e}"
                    )

            await asyncio.sleep(300)

        except Exception as e:
            loguru.logger.exception(f"Error in retry worker: {e}")
            await asyncio.sleep(60)
