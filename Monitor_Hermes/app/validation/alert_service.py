"""
Alert service with retry mechanism.
Sends alerts to Atlas API with pending queue on failure.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import httpx
import loguru

from app.clients.atlas import atlas_client
from app.persistence.mongo import save_pending_alert
from app.persistence.models import PendingAlert
from app.validation.measurement_validator import MeasurementViolation


def build_alert_message(
    dev_eui: str,
    device_name: str,
    violations: List[MeasurementViolation],
) -> Dict[str, str]:
    if len(violations) == 1:
        v = violations[0]
        exceeded = "below minimum" if v.limit_type == "min" else "above maximum"
        title = f"⚠️ {v.unit.capitalize()} Alert: {device_name}"
        message = (
            f"{v.unit.capitalize()} {exceeded} limit on {v.channel}. "
            f"Value: {v.value}, Limit: {v.limit_value}"
        )
    else:
        title = f"⚠️ Multiple Alerts: {device_name}"
        message = f"{len(violations)} measurement violations detected"

    return {"title": title, "message": message}


def build_atlas_payload(
    dev_eui: str,
    device_name: str,
    violations: List[MeasurementViolation],
) -> Dict[str, Any]:
    alert_msg = build_alert_message(dev_eui, device_name, violations)

    if len(violations) == 1:
        v = violations[0]
        kpi_summary = f"📊 {v.unit.upper()}: {v.value} (Limit: {v.limit_value}) | Channel: {v.channel}"
    else:
        units_affected = ", ".join(set(v.unit for v in violations))
        kpi_summary = (
            f"📊 {len(violations)} violations detected | Affected: {units_affected}"
        )

    message_with_kpi = f"{alert_msg['message']}\n\n{kpi_summary}"

    return {
        "title": alert_msg["title"],
        "message": message_with_kpi,
        "type": "warning",
        "dev_eui": dev_eui,
    }


async def send_alert_with_fallback(
    dev_eui: str,
    device_name: str,
    violations: List[MeasurementViolation],
    user_ids: List[str],
    db,
) -> Dict[str, Any]:
    atlas_payload = build_atlas_payload(dev_eui, device_name, violations)

    try:
        response = await atlas_client.post(
            "/api/v1/notifications/notifications/alert/",
            json=atlas_payload,
            timeout=5.0,
        )

        loguru.logger.info(f"✅ Alert sent to Atlas for device {dev_eui}")
        return {"method": "atlas", "success": True}

    except (httpx.HTTPError, httpx.TimeoutException) as e:
        loguru.logger.warning(f"⚠️ Atlas unreachable: {e}. Queuing alert for retry...")

        stored_user_id = user_ids[0] if user_ids else ""

        pending_alert = PendingAlert(
            dev_eui=dev_eui,
            user_id=stored_user_id,
            alert_data=atlas_payload,
            created_at=datetime.now(timezone.utc),
            sent_via_websocket=False,
        )

        try:
            await save_pending_alert(db, pending_alert)
            loguru.logger.info(
                f"📋 Alert queued for retry. Device: {dev_eui}"
            )
        except Exception as queue_error:
            loguru.logger.exception(f"Failed to queue alert: {queue_error}")

        return {
            "method": "queued",
            "success": False,
            "queued_for_retry": True,
        }
