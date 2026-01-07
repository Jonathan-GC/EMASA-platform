"""
Main validation orchestrator.
Coordinates measurement validation and alert sending.
"""

from typing import Dict, Any
import loguru

from app.validation.measurement_cache import get_or_fetch_measurement_configs
from app.validation.measurement_validator import validate_measurements
from app.validation.alert_service import send_alert_with_fallback
from app.validation.rate_limiter import should_send_alert
from app.persistence.device_mapping import get_user_ids_for_alert


async def validate_and_alert_if_needed(message: Dict[str, Any], db) -> None:
    """
    Main validation orchestrator.
    Called by redis_worker after saving message.
    """
    dev_eui = message.get("dev_eui")
    tenant_id = message.get("tenant_id")
    device_name = message.get("device_name", dev_eui)
    payload = message.get("payload", {})

    if not dev_eui or not tenant_id:
        return

    try:
        configs = await get_or_fetch_measurement_configs(dev_eui, db)

        if not configs:
            loguru.logger.debug(
                f"No measurement configs for {dev_eui}. Skipping validation."
            )
            return

        violations = validate_measurements(payload, configs)

        if not violations:
            return

        loguru.logger.info(f"Found {len(violations)} violations for {dev_eui}")

        violated_units = set(v.unit for v in violations)

        for unit in violated_units:
            can_send = await should_send_alert(dev_eui, unit)

            if not can_send:
                loguru.logger.info(
                    f"Skipping alert for {dev_eui}:{unit} - cooldown active"
                )
                continue

            user_ids = await get_user_ids_for_alert(db, dev_eui, tenant_id)

            if not user_ids:
                loguru.logger.info(
                    f"No user mapping for {dev_eui}. Atlas will route, but WebSocket fallback unavailable."
                )

            unit_violations = [v for v in violations if v.unit == unit]

            await send_alert_with_fallback(
                dev_eui=dev_eui,
                device_name=device_name,
                violations=unit_violations,
                user_ids=user_ids,
                db=db,
            )

    except Exception as e:
        loguru.logger.exception(f"Error in validation orchestrator for {dev_eui}: {e}")
