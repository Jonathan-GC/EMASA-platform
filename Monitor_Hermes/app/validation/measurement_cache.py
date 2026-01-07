"""
Measurement configuration cache management.
Handles fetching configs from Atlas API and caching in MongoDB.
"""

from typing import Optional, List
from datetime import datetime, timezone
import httpx
import loguru

from app.clients.atlas import atlas_client
from app.persistence.mongo import (
    get_device_measurement_configs,
    save_device_measurement_configs,
)
from app.persistence.models import MeasurementConfig


async def get_or_fetch_measurement_configs(
    dev_eui: str, db
) -> Optional[List[MeasurementConfig]]:
    """
    Get measurement configs from cache or fetch from Atlas API.
    First message from device triggers Atlas fetch and MongoDB cache.
    """
    cached = await get_device_measurement_configs(db, dev_eui)

    if cached:
        loguru.logger.debug(f"Using cached configs for {dev_eui}")
        return cached.configs

    loguru.logger.info(f"No cached configs for {dev_eui}. Fetching from Atlas...")

    try:
        response = await atlas_client.get(
            "/api/v1/infrastructure/device/measurements_by_dev_eui/",
            params={"dev_eui": dev_eui},
            timeout=5.0,
        )

        configs_data = response.json()

        if not configs_data or not isinstance(configs_data, list):
            loguru.logger.warning(f"Empty or invalid configs from Atlas for {dev_eui}")
            return None

        configs = [MeasurementConfig(**config) for config in configs_data]

        await save_device_measurement_configs(db, dev_eui, configs)

        loguru.logger.info(f"Fetched and cached {len(configs)} configs for {dev_eui}")

        return configs

    except httpx.HTTPError as e:
        loguru.logger.warning(
            f"Atlas API error fetching configs for {dev_eui}: {e}. Skipping validation."
        )
        return None

    except Exception as e:
        loguru.logger.exception(f"Unexpected error fetching configs for {dev_eui}: {e}")
        return None


async def force_refresh_measurement_configs(dev_eui: str, db) -> bool:
    """
    Force refresh of measurement configs from Atlas API.
    Used by synchronization endpoints.
    """
    loguru.logger.info(f"Force refreshing configs for {dev_eui}...")

    try:
        response = await atlas_client.get(
            "/api/v1/infrastructure/device/measurements_by_dev_eui/",
            params={"dev_eui": dev_eui},
            timeout=5.0,
        )

        configs_data = response.json()

        if not isinstance(configs_data, list):
            loguru.logger.warning(f"Invalid configs format from Atlas for {dev_eui}")
            return False

        configs = [MeasurementConfig(**config) for config in configs_data]

        await save_device_measurement_configs(db, dev_eui, configs)

        loguru.logger.info(f"Refreshed and cached {len(configs)} configs for {dev_eui}")
        return True

    except Exception as e:
        loguru.logger.exception(f"Failed to force refresh configs for {dev_eui}: {e}")
        return False
