"""
WebSocket notification helpers.
Reusable functions for sending notifications to users via WebSocket.
"""

import loguru
from typing import Optional, Dict, Any
from app.ws.manager import manager


async def notify_user(
    user_id: str | int,
    title: str,
    message: str,
    type: str = "info",
    extra_data: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    Send a notification to a user via WebSocket.

    Args:
        user_id: The ID of the user to notify (will be converted to string)
        title: The notification title
        message: The notification message content
        type: The notification type (info, warning, error, success)
        extra_data: Optional additional data to include in the notification payload

    Returns:
        bool: True if notification was sent successfully, False otherwise

    Example:
        >>> await notify_user(
        ...     user_id=1,
        ...     title="Device Alert",
        ...     message="Temperature threshold exceeded",
        ...     type="warning",
        ...     extra_data={"device_id": "ABC123", "value": 45.2}
        ... )
    """
    payload = {
        "channel": "notifications",
        "title": title,
        "message": message,
        "type": type,
    }

    # Add extra data if provided
    if extra_data:
        payload.update(extra_data)

    try:
        await manager.send_to_user(str(user_id), payload)
        loguru.logger.debug(f"Notification sent to user {user_id}: {title}")
        return True
    except Exception as e:
        loguru.logger.exception(
            f"Failed to send notification to user {user_id} via websocket: {e}"
        )
        return False


async def notify_users(
    user_ids: list[str | int],
    title: str,
    message: str,
    type: str = "info",
    extra_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, bool]:
    """
    Send a notification to multiple users via WebSocket.

    Args:
        user_ids: List of user IDs to notify
        title: The notification title
        message: The notification message content
        type: The notification type (info, warning, error, success)
        extra_data: Optional additional data to include in the notification payload

    Returns:
        dict: Dictionary mapping user_id to success status (True/False)

    Example:
        >>> results = await notify_users(
        ...     user_ids=[1, 2, 3],
        ...     title="System Maintenance",
        ...     message="Scheduled maintenance in 1 hour",
        ...     type="info"
        ... )
        >>> print(results)  # {1: True, 2: True, 3: False}
    """
    results = {}
    for user_id in user_ids:
        success = await notify_user(user_id, title, message, type, extra_data)
        results[str(user_id)] = success
    return results


async def notify_info(user_id: str | int, title: str, message: str, **kwargs) -> bool:
    """
    Send an info notification to a user.

    Shorthand for notify_user with type="info".
    """
    return await notify_user(
        user_id, title, message, type="info", extra_data=kwargs or None
    )


async def notify_warning(
    user_id: str | int, title: str, message: str, **kwargs
) -> bool:
    """
    Send a warning notification to a user.

    Shorthand for notify_user with type="warning".
    """
    return await notify_user(
        user_id, title, message, type="warning", extra_data=kwargs or None
    )


async def notify_error(user_id: str | int, title: str, message: str, **kwargs) -> bool:
    """
    Send an error notification to a user.

    Shorthand for notify_user with type="error".
    """
    return await notify_user(
        user_id, title, message, type="error", extra_data=kwargs or None
    )


async def notify_success(
    user_id: str | int, title: str, message: str, **kwargs
) -> bool:
    """
    Send a success notification to a user.

    Shorthand for notify_user with type="success".
    """
    return await notify_user(
        user_id, title, message, type="success", extra_data=kwargs or None
    )
