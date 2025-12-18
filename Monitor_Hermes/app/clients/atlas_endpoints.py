"""
Atlas API Integration Documentation.

This module documents the Atlas API endpoints used by the measurement validation system.
The actual HTTP client is in app.clients.atlas.
"""

# =============================================================================
# MEASUREMENT CONFIGS ENDPOINT
# =============================================================================

"""
GET /api/v1/infrastructure/device/measurements_by_dev_eui/

Fetches measurement configuration for a specific device.

Query Parameters:
    dev_eui (str): Device EUI identifier

Response (200 OK):
    [
        {
            "id": "401806290ced96c0",
            "min": 10.5,
            "max": 25.3,
            "threshold": 20.0,
            "unit": "voltage"
        },
        {
            "id": "5f8a7b3c2e1d9a4f",
            "min": 0.0,
            "max": 5.0,
            "threshold": 1.0,
            "unit": "current"
        }
    ]

Usage Example:
    from app.clients.atlas import atlas_client
    
    response = await atlas_client.get(
        "/api/v1/infrastructure/device/measurements_by_dev_eui/",
        params={"dev_eui": "70b3d57ed006e15b"},
        timeout=5.0
    )
    configs = response.json()

Error Handling:
    - 404: Device not found or no configs available
    - 401: Invalid API key
    - 500: Internal server error
    - Timeout: Network issues or Atlas unavailable

Used by:
    - app.validation.measurement_cache.get_or_fetch_measurement_configs()
"""


# =============================================================================
# DEVICE USERS ENDPOINT
# =============================================================================

"""
GET /api/v1/infrastructure/device/get_users_for_device

Fetches users assigned to a specific device.

Query Parameters:
    dev_eui (str): Device EUI identifier

Response (200 OK):
    {
        "dev_eui": "70b3d57ed006e15b",
        "tenant_id": "5a8b9c7d2e3f1a4b",
        "assigned_users": [
            {"user_id": "1", "username": "admin"},
            {"user_id": "2", "username": "operator"}
        ]
    }

Usage Example:
    from app.clients.atlas import atlas_client
    
    response = await atlas_client.get(
        "/api/v1/infrastructure/device/get_users_for_device",
        params={"dev_eui": "70b3d57ed006e15b"}
    )
    data = response.json()

Used by:
    - app.persistence.device_mapping.get_device_user_mapping()
"""


# =============================================================================
# NOTIFICATION ALERT ENDPOINT
# =============================================================================

"""
POST /api/v1/support/notification/alert/

Sends a notification alert to Atlas for a specific user.

Request Body:
    {
        "title": "Alert Title",
        "message": "Alert message content",
        "type": "info|warning|error|success",
        "user": 1,
        "metadata": {
            "source": "monitor_hermes",
            "dev_eui": "70b3d57ed006e15b",
            "device_name": "Morbius",
            "violation_count": 2,
            "violations": [
                {
                    "unit": "voltage",
                    "channel": "ch1",
                    "value": 28.5,
                    "limit_type": "max",
                    "limit_value": 25.3,
                    "threshold": 20.0,
                    "timestamp": "2025-11-11T15:30:00Z"
                }
            ]
        }
    }

Response (200 OK):
    {
        "id": "7a2f9c8e1b5d3a6f",
        "status": "sent",
        "created_at": "2025-11-11T15:30:00Z"
    }

Usage Example:
    from app.clients.atlas import atlas_client
    
    alert_data = {
        "title": "Voltage Alert",
        "message": "Voltage exceeded maximum limit",
        "type": "warning",
        "user": "5a8b9c7d2e3f1a4b",
        "metadata": {...}
    }
    
    response = await atlas_client.post(
        "/api/v1/support/notification/alert/",
        json=alert_data,
        timeout=5.0
    )

Error Handling:
    - 400: Invalid request body
    - 401: Invalid API key
    - 404: User not found
    - 500: Internal server error
    - Timeout: Triggers fallback to WebSocket

Fallback Mechanism:
    If this endpoint fails:
    1. Send notification via WebSocket (notify_user)
    2. Save to pending_alerts collection in MongoDB
    3. Retry worker attempts resend every 5 minutes (max 3 attempts)

Used by:
    - app.validation.alert_service.send_alert_with_fallback()
    - app.workers.alert_retry_worker.retry_pending_alerts()
"""


# =============================================================================
# CLIENT USAGE
# =============================================================================

"""
The atlas_client singleton is available throughout the application:

    from app.clients.atlas import atlas_client
    
    # GET request
    response = await atlas_client.get(endpoint, params={...})
    
    # POST request
    response = await atlas_client.post(endpoint, json={...})
    
    # With error handling
    try:
        response = await atlas_client.get(endpoint, timeout=5.0)
        data = response.json()
    except httpx.HTTPError as e:
        logger.error(f"Atlas API error: {e}")
    except httpx.TimeoutException:
        logger.error("Atlas API timeout")

All requests automatically include:
    - X-API-Key header (from SERVICE_API_KEY env var)
    - Content-Type: application/json
    - Base URL (from ATLAS_HOST_URL env var)
"""
