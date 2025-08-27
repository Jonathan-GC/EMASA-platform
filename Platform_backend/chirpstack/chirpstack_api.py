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
                "source": gateway.location.source,
            },
        }
    }
    response = requests.post(CHIRPSTACK_GATEWAYS_URL, json=payload, headers=HEADERS)

    if response.status_code == 200:
        response_sync = requests.get(
            CHIRPSTACK_GATEWAYS_URL,
            headers=HEADERS,
            params={"tenant_id": gateway.workspace.tenant.cs_tenant_id, "limit": 100},
        )
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


def sync_api_user_chirpstack_creation(api_user):
    """
    Syncs an API user with Chirpstack.

    Args:
        api_user (APIUser): an APIUser object

    Returns:
        requests.Response: the response from the API
    """
    payload = {
        "password": api_user.password,
        "tenants": [
            {
                "isAdmin": api_user.is_tenant_admin,
                "isDeviceAdmin": api_user.is_tenant_device_admin,
                "isGatewayAdmin": api_user.is_tenant_gateway_admin,
                "tenantId": api_user.tenant.cs_tenant_id,
            }
        ],
        "user": {
            "email": api_user.email,
            "isActive": api_user.is_active,
            "isAdmin": api_user.is_admin,
            "note": api_user.note,
        },
    }
    response = requests.post(CHIRPSTACK_API_URL, json=payload, headers=HEADERS)

    if response.status_code == 200:
        api_id = response.json()["id"]
        api_user.cs_user_id = api_id
        api_user.sync_status = "SYNCED"
        api_user.last_synced_at = dt.datetime.now()
        api_user.save()
        return response
    else:
        api_user.sync_status = "ERROR"
        api_user.sync_error = response.text
        api_user.last_synced_at = dt.datetime.now()
        api_user.save()
        return response


def sync_device_profile_chirpstack_creation(device_profile):
    """
    Syncs a device profile with Chirpstack.

    Args:
        device_profile (DeviceProfile): a DeviceProfile object

    Returns:
        requests.Response: the response from the API
    """
    payload = {
        "deviceProfile": {
            "name": device_profile.name,
            "region": device_profile.region,
            "macVersion": device_profile.mac_version,
            "regParamRevision": device_profile.reg_param_revision,
            "supportsOtaa": device_profile.supports_otaa,
            "abpRx1Delay": device_profile.abp_rx1_delay,
            "abpRx1DrOffset": device_profile.abp_rx1_dr_offset,
            "abpRx2Dr": device_profile.abp_rx2_dr,
            "abpRx2Freq": device_profile.abp_rx2_freq,
            "supportsClassB": device_profile.supports_class_b,
            "supportsClassC": device_profile.supports_class_c,
            "payloadCodecRuntime": device_profile.payload_codec_runtime,
            "isRelay": device_profile.is_rlay,
            "isRelayEd": device_profile.is_rlay_ed,
            "tenantId": device_profile.tenant.cs_tenant_id
        }
    }
    response = requests.post(
        CHIRPSTACK_DEVICE_PROFILE_URL, json=payload, headers=HEADERS
    )
    print(response.request.url, response.request.body)
    
    if response.status_code == 200:
        api_id = response.json()["id"]
        device_profile.cs_device_profile_id = api_id
        device_profile.sync_status = "SYNCED"
        device_profile.last_synced_at = dt.datetime.now()
        device_profile.save()
        print(response.json())
        return response
    else:
        device_profile.sync_status = "ERROR"
        device_profile.sync_error = response.text
        device_profile.last_synced_at = dt.datetime.now()
        device_profile.save()
        print(response.text)
        return response
