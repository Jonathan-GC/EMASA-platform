import requests
from django.conf import settings
import datetime as dt

CHIRPSTACK_BASE_URL = settings.CHIRPSTACK_BASE_URL
CHIRPSTACK_JWT_TOKEN = settings.CHIRPSTACK_JWT_TOKEN

CHIRPSTACK_API_URL = CHIRPSTACK_BASE_URL + "/users"
CHIRPSTACK_TENANT_URL = CHIRPSTACK_BASE_URL + "/tenants"
CHIRPSTACK_GATEWAYS_URL = CHIRPSTACK_BASE_URL + "/gateways"
CHIRPSTACK_DEVICE_PROFILE_URL = CHIRPSTACK_BASE_URL + "/device-profiles"
CHIRPSTACK_DEVICE_URL = CHIRPSTACK_BASE_URL + "/devices"
CHIRPSTACK_APPLICATION_URL = CHIRPSTACK_BASE_URL + "/applications"

HEADERS = {
    "Authorization": f"Bearer {CHIRPSTACK_JWT_TOKEN}",
    "Content-Type": "application/json",
}


def sync_tenant_chirpstack_creation(tenant):
    """
    Syncs a tenant with Chirpstack.
    
    Args:
        tenant (Tenant): a Tenant object
    
    Returns:
        requests.Response: the response from the API
    """
    payload = {
        "tenant": {
            "name": tenant.name,
            "description": tenant.description,
            "canHaveGateways": tenant.subscription.can_have_gateways,
            "maxDeviceCount": tenant.subscription.max_device_count,
            "maxGatewayCount": tenant.subscription.max_gateway_count,
        }
    }
    response = requests.post(CHIRPSTACK_TENANT_URL, json=payload, headers=HEADERS)

    if response.status_code == 200:
        api_id = response.json()["id"]
        tenant.cs_tenant_id = api_id
        tenant.sync_status = "SYNCED"
        tenant.last_synced_at = dt.datetime.now()
        tenant.save()
        return response
    else:
        tenant.sync_status = "ERROR"
        tenant.sync_error = response.text
        tenant.last_synced_at = dt.datetime.now()
        tenant.save()
        return response

def sync_gateway_chirpstack_creation(gateway):
    """
    Syncs a gateway with Chirpstack.

    Args:
        gateway (Gateway): a Gateway object

    Returns:
        requests.Response: the response from the API
    """
    payload = {
        "gateway": {
            "gatewayId": gateway.cs_gateway_id,
            "name": gateway.name,
            "description": gateway.description,
            "statsInterval": gateway.stats_interval,
            "tenantId": gateway.workspace.tenant.cs_tenant_id,
            "location": {
                "accuracy": gateway.location.accuracy,
                "altitude": gateway.location.altitude,
                "latitude": gateway.location.latitude,
                "longitude": gateway.location.longitude,
                "source": gateway.location.source
            }
        }
    }
    response = requests.post(CHIRPSTACK_GATEWAYS_URL, json=payload, headers=HEADERS)

    if response.status_code == 200:
        response_sync = requests.get(CHIRPSTACK_GATEWAYS_URL, headers=HEADERS, params={"tenant_id": gateway.workspace.tenant.cs_tenant_id, "limit": 100})
        print(response_sync.json(), response_sync.request.url)
        data = response_sync.json().get("result", [])
        for result in data:
            if result["gatewayId"] == gateway.cs_gateway_id:
                gateway.state = result["state"]
                gateway.last_seen_at = result["lastSeenAt"]
                gateway.sync_status = "SYNCED"
                gateway.last_synced_at = dt.datetime.now()
                gateway.save()
                break
        return response
    else:
        gateway.sync_status = "ERROR"
        gateway.sync_error = response.text
        gateway.last_synced_at = dt.datetime.now()
        gateway.save()
        return response