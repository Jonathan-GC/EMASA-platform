"""
Device-to-user mapping utilities.
"""

from typing import Optional, List
from app.persistence.mongo import get_users_for_device
import loguru


async def get_user_ids_for_alert(db, dev_eui: str, tenant_id: str) -> List[str]:
    """
    Get user IDs to notify for a device alert.

    Priority:
    1. Check device_user_mapping in MongoDB
    2. Fallback: derive from tenant (Atlas API call would go here)
    3. Fallback: return empty list (no notifications)
    """
    mapping = await get_users_for_device(db, dev_eui)

    if mapping:
        return mapping.assigned_users if mapping.assigned_users else []

    loguru.logger.warning(
        f"No user mapping found for device {dev_eui}. Skipping alert."
    )
    return []


async def get_primary_user_for_alert(db, dev_eui: str, tenant_id: str) -> Optional[str]:
    """
    Get primary user ID for device alerts.
    """
    mapping = await get_users_for_device(db, dev_eui)

    if mapping and mapping.primary_user:
        return mapping.primary_user

    loguru.logger.warning(f"No primary user found for device {dev_eui}")
    return None
