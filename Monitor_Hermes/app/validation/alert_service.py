"""
Alert service with fallback mechanism.
Sends alerts to Atlas API with WebSocket fallback.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import httpx
import loguru

from app.clients.atlas import atlas_client
from app.ws.helpers import notify_warning
from app.persistence.mongo import save_pending_alert
from app.persistence.models import PendingAlert
from app.validation.measurement_validator import MeasurementViolation


def build_alert_message(
    dev_eui: str,
    device_name: str,
    violations: List[MeasurementViolation],
) -> Dict[str, str]:
    """
    Build user-friendly alert message from violations.
    """
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
    """
    Build detailed alert payload for Atlas API.
    Atlas routes to users based on dev_eui, no user_id needed.
    """
    alert_msg = build_alert_message(dev_eui, device_name, violations)

    metadata_detail = {
        "source": "monitor_hermes",
        "device_name": device_name,
        "violation_count": len(violations),
        "violations": [v.to_dict() for v in violations],
    }

    import json

    message_with_metadata = (
        f"{alert_msg['message']}\n\nDetails: {json.dumps(metadata_detail, indent=2)}"
    )

    return {
        "title": alert_msg["title"],
        "message": message_with_metadata,
        "type": "warning",
        "dev_eui": dev_eui,
    }


async def send_alert_with_fallback(
    dev_eui: str,
    device_name: str,
    violations: List[MeasurementViolation],
    user_id: Optional[int],
    db,
) -> Dict[str, Any]:
    """
    Send alert with fallback mechanism.
    PRIMARY: Atlas API (routes by dev_eui, no user_id needed)
    FALLBACK: WebSocket (requires user_id from device_user_mapping)
    """
    atlas_payload = build_atlas_payload(dev_eui, device_name, violations)

    try:
        response = await atlas_client.post(
            "/api/v1/support/notification/alert/",
            json=atlas_payload,
            timeout=5.0,
        )

        loguru.logger.info(f"✅ Alert sent to Atlas for device {dev_eui}")
        return {"method": "atlas", "success": True}

    except (httpx.HTTPError, httpx.TimeoutException) as e:
        loguru.logger.warning(f"⚠️ Atlas unreachable: {e}. Activating PLAN B...")

        alert_msg = build_alert_message(dev_eui, device_name, violations)

        ws_success = False

        if user_id:
            try:
                ws_success = await notify_warning(
                    user_id=user_id,
                    title=alert_msg["title"],
                    message=alert_msg["message"],
                    device_name=device_name,
                    dev_eui=dev_eui,
                    alert_type="measurement_violation",
                )

                if ws_success:
                    loguru.logger.info(
                        f"✅ Alert sent via WebSocket (PLAN B) for user {user_id}"
                    )
                else:
                    loguru.logger.warning(
                        f"⚠️ WebSocket delivery failed. User {user_id} not connected."
                    )

            except Exception as fallback_error:
                loguru.logger.exception(f"❌ PLAN B WebSocket failed: {fallback_error}")
        else:
            loguru.logger.warning(
                f"⚠️ No user_id mapping for {dev_eui}. Cannot send WebSocket fallback."
            )

        pending_alert = PendingAlert(
            dev_eui=dev_eui,
            user_id=user_id or 0,
            alert_data=atlas_payload,
            created_at=datetime.now(timezone.utc),
            sent_via_websocket=ws_success,
        )

        try:
            await save_pending_alert(db, pending_alert)
            loguru.logger.info(
                f"📋 Alert queued for retry. WebSocket: {ws_success}, Device: {dev_eui}"
            )
        except Exception as queue_error:
            loguru.logger.exception(f"Failed to queue alert: {queue_error}")

        return {
            "method": "websocket" if ws_success else "queued",
            "success": ws_success,
            "queued_for_retry": True,
        }
