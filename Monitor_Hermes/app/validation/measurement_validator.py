"""
Measurement validation logic.
Validates device measurements against configured limits.
"""

from typing import List, Dict, Any, Optional
import loguru

from app.persistence.models import MeasurementConfig


class MeasurementViolation:
    def __init__(
        self,
        unit: str,
        channel: str,
        value: float,
        limit_type: str,
        limit_value: float,
        threshold: float,
        timestamp: str,
    ):
        self.unit = unit
        self.channel = channel
        self.value = value
        self.limit_type = limit_type
        self.limit_value = limit_value
        self.threshold = threshold
        self.timestamp = timestamp

    def to_dict(self) -> Dict[str, Any]:
        return {
            "unit": self.unit,
            "channel": self.channel,
            "value": self.value,
            "limit_type": self.limit_type,
            "limit_value": self.limit_value,
            "threshold": self.threshold,
            "timestamp": self.timestamp,
        }


def validate_measurements(
    payload: Dict[str, Any], configs: List[MeasurementConfig]
) -> List[MeasurementViolation]:
    """
    Validate measurements in payload against configured limits.
    Returns list of violations found.
    """
    violations = []

    measurements = payload.get("measurements")
    if not measurements or not isinstance(measurements, dict):
        loguru.logger.debug("No measurements field in payload")
        return violations

    for config in configs:
        unit = config.unit

        if unit not in measurements:
            continue

        unit_data = measurements[unit]
        if not isinstance(unit_data, dict):
            continue

        for channel in ["ch1", "ch2", "ch3"]:
            if channel not in unit_data:
                continue

            readings = unit_data[channel]
            if not isinstance(readings, list):
                continue

            for reading in readings:
                if not isinstance(reading, dict):
                    continue

                value = reading.get("value")
                timestamp = reading.get("time")

                if value is None:
                    continue

                try:
                    value = float(value)
                except (ValueError, TypeError):
                    continue

                if value < config.min:
                    violations.append(
                        MeasurementViolation(
                            unit=unit,
                            channel=channel,
                            value=value,
                            limit_type="min",
                            limit_value=config.min,
                            threshold=config.threshold,
                            timestamp=timestamp or "",
                        )
                    )
                    loguru.logger.warning(
                        f"Violation: {unit} {channel} value {value} < min {config.min}"
                    )

                elif value > config.max:
                    violations.append(
                        MeasurementViolation(
                            unit=unit,
                            channel=channel,
                            value=value,
                            limit_type="max",
                            limit_value=config.max,
                            threshold=config.threshold,
                            timestamp=timestamp or "",
                        )
                    )
                    loguru.logger.warning(
                        f"Violation: {unit} {channel} value {value} > max {config.max}"
                    )

    return violations
