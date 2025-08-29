import requests
from django.conf import settings
import datetime as dt

from organizations.models import Tenant

import logging

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


# Tenants
def sync_tenant_get(tenant):
    """
    Syncs a tenant with Chirpstack.

    Args:
        tenant (Tenant): a Tenant object

    Returns:
        requests.Response: the response from the API

    Side Effects:
        Updates tenant fields such as cs_tenant_id, sync_status, sync_error, and last_synced_at.

    Raises:
        May set tenant.sync_status to "ERROR" and tenant.sync_error if the API call fails.
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
    tenant_id = tenant.cs_tenant_id

    response = None

    url = f"{CHIRPSTACK_TENANT_URL}/{tenant_id}"
    response = requests.get(url, headers=HEADERS)

    if response.status_code == 200:
        logging.info(f"Tenant found in Chirpstack: {tenant.name}")
        tenant.sync_status = "SYNCED"
        if tenant.sync_error != "":
            tenant.sync_error = ""
        tenant.last_synced_at = dt.datetime.now()
        tenant.save()
        return response
    elif tenant.cs_tenant_id == "" or tenant.cs_tenant_id is None:
        list_response = requests.get(
            CHIRPSTACK_TENANT_URL,
            headers=HEADERS,
            params={"limit": 100},
        )

        if list_response.status_code == 200:
            results = list_response.json().get("result", [])
            match = next((t for t in results if t["name"] == tenant.name), None)
            if match:
                tenant.cs_tenant_id = match["id"]
                tenant.sync_status = "SYNCED"
                tenant.sync_error = ""
                tenant.last_synced_at = dt.datetime.now()
                tenant.save()
                return list_response
            else:
                response = requests.post(
                    CHIRPSTACK_TENANT_URL, json=payload, headers=HEADERS
                )
                tenant.cs_tenant_id = response.json()["id"]
                tenant.sync_status = "SYNCED"
                tenant.sync_error = ""
                tenant.last_synced_at = dt.datetime.now()
                tenant.save()
                return list_response
    else:
        logging.error(f"Error getting tenant: {tenant.name} \n {response.text}")
        tenant.sync_status = "ERROR"
        tenant.sync_error = response.text
        tenant.last_synced_at = dt.datetime.now()
        tenant.save()
        return response


def sync_tenant_create(tenant):
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
        logging.info(f"Tenant created in Chirpstack: {tenant.name}")
        tenant.cs_tenant_id = response.json()["id"]
        tenant.sync_status = "SYNCED"
        tenant.sync_error = ""
        tenant.last_synced_at = dt.datetime.now()
        tenant.save()
        return response
    else:
        logging.error(f"Error creating tenant: {tenant.name} \n {response.text}")
        tenant.sync_status = "ERROR"
        tenant.sync_error = response.text
        tenant.last_synced_at = dt.datetime.now()
        tenant.save()
        return response


def sync_tenant_update(tenant):
    """
    Syncs a tenant with Chirpstack.

    If the tenant doesn't have a Chirpstack ID, it creates a new tenant.
    If the tenant has a Chirpstack ID, it updates the existing tenant.

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

    url = f"{CHIRPSTACK_TENANT_URL}/{tenant.cs_tenant_id}"

    response = sync_tenant_get(tenant)

    if response.status_code == 200:
        response = requests.put(url, json=payload, headers=HEADERS)
    elif tenant.cs_tenant_id == "" or tenant.cs_tenant_id is None:
        response = requests.post(CHIRPSTACK_TENANT_URL, json=payload, headers=HEADERS)

    if response.status_code == 200:
        logging.info(f"Tenant updated in Chirpstack: {tenant.name}")
        tenant.sync_status = "SYNCED"
        tenant.sync_error = ""
        tenant.last_synced_at = dt.datetime.now()
        tenant.save()
        return response
    else:
        logging.error(f"Error updating tenant: {tenant.name} \n {response.text}")
        tenant.sync_status = "ERROR"
        tenant.sync_error = response.text
        tenant.last_synced_at = dt.datetime.now()
        tenant.save()
        return response


def sync_tenant_destroy(tenant):
    """
    Deletes a tenant in Chirpstack.

    Args:
        tenant (Tenant): a Tenant object

    Returns:
        requests.Response: the response from the API
    """
    url = f"{CHIRPSTACK_TENANT_URL}/{tenant.cs_tenant_id}"
    response = requests.delete(url, headers=HEADERS)

    if response.status_code == 200:
        logging.info(f"Tenant deleted in Chirpstack")
        return response
    else:
        logging.error(f"Error deleting tenant try to delete it manually.")
        return response


# Gateways
def sync_gateway_get(gateway):
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
    response = requests.get(
        CHIRPSTACK_GATEWAYS_URL,
        headers=HEADERS,
        params={"tenant_id": gateway.workspace.tenant.cs_tenant_id, "limit": 100},
    )

    if response.status_code == 200:
        data = response.json().get("result", [])
        gw_data = next(
            (g for g in data if g["gatewayId"] == gateway.cs_gateway_id), None
        )

        if gw_data:
            gateway.state = gw_data.get("state", gateway.state)
            gateway.last_seen_at = gw_data.get("lastSeenAt", gateway.last_seen_at)
            if gateway.sync_error != "":
                gateway.sync_error = ""
            gateway.sync_status = "SYNCED"
            gateway.last_synced_at = dt.datetime.now()
            gateway.save()
        else:
            response = requests.post(
                CHIRPSTACK_GATEWAYS_URL, json=payload, headers=HEADERS
            )
            if response.status_code == 200:
                gateway.sync_status = "SYNCED"
                if gateway.sync_error != "":
                    gateway.sync_error = ""
                gateway.last_synced_at = dt.datetime.now()
                gateway.save()
    else:
        gateway.sync_status = "ERROR"
        gateway.sync_error = response.text
        gateway.last_synced_at = dt.datetime.now()
        gateway.save()

    return response


def sync_gateway_create(gateway):
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
        gateway.sync_status = "SYNCED"
        if gateway.sync_error != "":
            gateway.sync_error = ""
        gateway.last_synced_at = dt.datetime.now()
        gateway.save()
    else:
        gateway.sync_status = "ERROR"
        gateway.sync_error = response.text
        gateway.last_synced_at = dt.datetime.now()
        gateway.save()

    return response


def sync_gateway_update(gateway):
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

    response = sync_gateway_get(gateway)

    if response.status_code == 200:
        response = requests.put(
            f"{CHIRPSTACK_GATEWAYS_URL}/{gateway.cs_gateway_id}",
            json=payload,
            headers=HEADERS,
        )
    else:
        response = requests.post(CHIRPSTACK_GATEWAYS_URL, json=payload, headers=HEADERS)

    if response.status_code == 200:
        gateway.sync_status = "SYNCED"
        if gateway.sync_error != "":
            gateway.sync_error = ""
        gateway.last_synced_at = dt.datetime.now()
        gateway.save()
    else:
        gateway.sync_status = "ERROR"
        gateway.sync_error = response.text
        gateway.last_synced_at = dt.datetime.now()
        gateway.save()

    return response


def sync_gateway_destroy(gateway):
    response = requests.delete(
        f"{CHIRPSTACK_GATEWAYS_URL}/{gateway.cs_gateway_id}",
        headers=HEADERS,
    )
    if response.status_code == 200:
        logging.info(f"Gateway deleted in Chirpstack")
        return response
    else:
        logging.error(f"Error deleting gateway try to delete it manually.")
        return response


# Chirpstack user
def sync_api_user_get(api_user):
    """
    Syncs an API user with Chirpstack by searching for a user with the same email.

    If a match is found, it updates the user in the database with the Chirpstack user id and sync status.
    If a match is not found, it creates a new user in Chirpstack and updates the user in the database with the Chirpstack user id and sync status.

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

    response = requests.get(
        CHIRPSTACK_API_URL,
        headers=HEADERS,
        params={"limit": 100},
    )

    if response.status_code == 200:
        results = response.json().get("result", [])
        match = next((u for u in results if u["email"] == api_user.email), None)

        if match:
            logging.info(f"User found in Chirpstack")
            api_user.cs_user_id = match["id"]
            api_user.is_active = match.get("isActive", api_user.is_active)
            api_user.is_admin = match.get("isAdmin", api_user.is_admin)
            api_user.sync_status = "SYNCED"
            api_user.sync_error = ""
            api_user.last_synced_at = dt.datetime.now()
            api_user.save()
        elif api_user.cs_user_id or api_user.cs_user_id.strip() == "":
            logging.info(f"User not found in Chirpstack")
            response = requests.post(CHIRPSTACK_API_URL, json=payload, headers=HEADERS)
            if response.status_code == 200:
                api_id = response.json()["id"]
                api_user.cs_user_id = api_id
                api_user.sync_status = "SYNCED"
                api_user.sync_error = (
                    "User not found in Chirpstack but is created and synced now"
                )
                api_user.last_synced_at = dt.datetime.now()
                api_user.save()
            else:
                api_user.sync_status = "PENDING"
                api_user.sync_error = (
                    "User not found in Chirpstack and cs_user_id is not empty"
                )
                api_user.last_synced_at = dt.datetime.now()
                api_user.save()
        else:
            logging.info(f"User not found in Chirpstack and cs_user_id is not empty")
            api_user.sync_status = "PENDING"
            api_user.sync_error = (
                "User not found in Chirpstack and cs_user_id is not empty"
            )
            api_user.last_synced_at = dt.datetime.now()
            api_user.save()


def sync_api_user_create(api_user):
    """
    Syncs an API user with Chirpstack.

    Args:
        api_user (ApiUser): an ApiUser object

    Returns:
        requests.Response: the response from the API

    Side Effects:
        Updates API user fields such as cs_user_id, sync_status, sync_error, and last_synced_at.
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
        api_user.sync_error = ""
        api_user.last_synced_at = dt.datetime.now()
        api_user.save()
    else:
        api_user.sync_status = "ERROR"
        api_user.sync_error = response.text
        api_user.last_synced_at = dt.datetime.now()
        api_user.save()

    return response


def sync_api_user_update(api_user):
    """
    Syncs an ApiUser with Chirpstack.

    Args:
        api_user (ApiUser): an ApiUser object

    Returns:
        requests.Response: the response from the API

    Side Effects:
        Updates api_user fields such as cs_user_id, sync_status, sync_error, and last_synced_at.

    Raises:
        May set api_user.sync_status to "ERROR" and api_user.sync_error if the API call fails.
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
    if not api_user.cs_user_id or api_user.cs_user_id.strip() == "":
        search_resp = requests.get(
            CHIRPSTACK_API_URL,
            headers=HEADERS,
            params={"limit": 100},
        )
        if search_resp.status_code == 200:
            results = search_resp.json().get("result", [])
            match = next((u for u in results if u["email"] == api_user.email), None)
            if match:
                api_user.cs_user_id = match["id"]
                api_user.save()

    if api_user.cs_user_id or api_user.cs_user_id.strip() != "":
        url = f"{CHIRPSTACK_API_URL}/{api_user.cs_user_id}"
        response = requests.put(url, json=payload, headers=HEADERS)
        if response.status_code == 200:
            api_user.sync_status = "SYNCED"
            api_user.sync_error = ""
            api_user.last_synced_at = dt.datetime.now()
            api_user.save()
        else:
            api_user.sync_status = "ERROR"
            api_user.sync_error = response.text
            api_user.last_synced_at = dt.datetime.now()
            api_user.save()
    else:
        response = requests.post(CHIRPSTACK_API_URL, json=payload, headers=HEADERS)

        if response.status_code == 200:
            api_id = response.json()["id"]
            api_user.cs_user_id = api_id
            api_user.sync_status = "SYNCED"
            api_user.sync_error = ""
            api_user.last_synced_at = dt.datetime.now()
            api_user.save()
        else:
            api_user.sync_status = "ERROR"
            api_user.sync_error = response.text
            api_user.last_synced_at = dt.datetime.now()
            api_user.save()


def sync_api_user_destroy(api_user):
    """
    Syncs a DeviceProfile with Chirpstack.

    Args:
        api_user (ApiUser): an ApiUser object

    Returns:
        requests.Response: the response from the API
    """
    if api_user.cs_user_id:
        url = f"{CHIRPSTACK_API_URL}/{api_user.cs_user_id}"
        response = requests.delete(url, headers=HEADERS)
        if response.status_code == 200:
            logging.info(f"User deleted in Chirpstack")
            return response
        else:
            logging.error(
                f"Error deleting user, user not found or try to delete it manually."
            )
            return response

# DeviceProfile
def chirpstack_device_profile_get(device_profile):
    payload = {
        "deviceProfile": {
            "name": device_profile.name,
            "description": device_profile.description,
            "region": device_profile.region,
            "macVersion": device_profile.mac_version,
            "regParamsRevision": device_profile.reg_param_revision,
            "supportsOtaa": device_profile.supports_otaa,
            "abpRx1Delay": device_profile.abp_rx1_delay,
            "abpRx1DrOffset": device_profile.abp_rx1_dr_offset,
            "abpRx2Dr": device_profile.abp_rx2_dr,
            "abpRx2Freq": device_profile.abp_rx2_freq,
            "supportsClassB": device_profile.supports_class_b,
            "supportsClassC": device_profile.supports_class_c,
            "payloadCodecRuntime": device_profile.payload_codec_runtime,
            "payloadCodecScript": device_profile.payload_codec_script,
            "isRelay": device_profile.is_rlay,
            "isRelayEd": device_profile.is_rlay_ed,
            "tenantId": device_profile.tenant.cs_tenant_id,
        }
    }
    url = f"{CHIRPSTACK_DEVICE_PROFILE_URL}/{device_profile.cs_device_profile_id}"

    response = requests.get(url, headers=HEADERS)

    if response.status_code == 200:
        device_profile.sync_status = "SYNCED"
        device_profile.sync_error = ""
        device_profile.last_synced_at = dt.datetime.now()
        device_profile.save()
    elif (
        device_profile.cs_device_profile_id is None
        or device_profile.cs_device_profile_id == ""
    ):
        response = requests.post(
            CHIRPSTACK_DEVICE_PROFILE_URL, json=payload, headers=HEADERS
        )
        if response.status_code == 200:
            device_profile.cs_device_profile_id = response.json()["id"]
            device_profile.save()
            device_profile.sync_status = "SYNCED"
            device_profile.sync_error = ""
            device_profile.last_synced_at = dt.datetime.now()
            device_profile.save()
        else:
            device_profile.sync_status = "ERROR"
            device_profile.sync_error = response.text
            device_profile.last_synced_at = dt.datetime.now()
            device_profile.save()
    else:
        device_profile.sync_status = "ERROR"
        device_profile.sync_error = response.text
        device_profile.last_synced_at = dt.datetime.now()
        device_profile.save()

    return response


def chirpstack_device_profile_create(device_profile):
    payload = {
        "deviceProfile": {
            "name": device_profile.name,
            "description": device_profile.description,
            "region": device_profile.region,
            "macVersion": device_profile.mac_version,
            "regParamsRevision": device_profile.reg_param_revision,
            "supportsOtaa": device_profile.supports_otaa,
            "abpRx1Delay": device_profile.abp_rx1_delay,
            "abpRx1DrOffset": device_profile.abp_rx1_dr_offset,
            "abpRx2Dr": device_profile.abp_rx2_dr,
            "abpRx2Freq": device_profile.abp_rx2_freq,
            "supportsClassB": device_profile.supports_class_b,
            "supportsClassC": device_profile.supports_class_c,
            "payloadCodecRuntime": device_profile.payload_codec_runtime,
            "payloadCodecScript": device_profile.payload_codec_script,
            "isRelay": device_profile.is_rlay,
            "isRelayEd": device_profile.is_rlay_ed,
            "tenantId": device_profile.tenant.cs_tenant_id,
        }
    }
    response = requests.post(
        CHIRPSTACK_DEVICE_PROFILE_URL, json=payload, headers=HEADERS
    )

    if response.status_code == 200:
        device_profile.cs_device_profile_id = response.json()["id"]
        device_profile.save()
        device_profile.sync_status = "SYNCED"
        device_profile.sync_error = ""
        device_profile.last_synced_at = dt.datetime.now()
        device_profile.save()
    else:
        device_profile.sync_status = "ERROR"
        device_profile.sync_error = response.text
        device_profile.last_synced_at = dt.datetime.now()
        device_profile.save()

    return response


def chirpstack_device_profile_update(device_profile):
    """
    Syncs a DeviceProfile with Chirpstack.

    Args:
        device_profile (DeviceProfile): a DeviceProfile object

    Returns:
        requests.Response: the response from the API

    Side Effects:
        Updates device_profile fields such as cs_device_profile_id, sync_status, sync_error, and last_synced_at.

    Raises:
        May set device_profile.sync_status to "ERROR" and device_profile.sync_error if the API call fails.
    """
    payload = {
        "deviceProfile": {
            "name": device_profile.name,
            "description": device_profile.description,
            "region": device_profile.region,
            "macVersion": device_profile.mac_version,
            "regParamsRevision": device_profile.reg_param_revision,
            "supportsOtaa": device_profile.supports_otaa,
            "abpRx1Delay": device_profile.abp_rx1_delay,
            "abpRx1DrOffset": device_profile.abp_rx1_dr_offset,
            "abpRx2Dr": device_profile.abp_rx2_dr,
            "abpRx2Freq": device_profile.abp_rx2_freq,
            "supportsClassB": device_profile.supports_class_b,
            "supportsClassC": device_profile.supports_class_c,
            "payloadCodecRuntime": device_profile.payload_codec_runtime,
            "payloadCodecScript": device_profile.payload_codec_script,
            "isRelay": device_profile.is_rlay,
            "isRelayEd": device_profile.is_rlay_ed,
            "tenantId": device_profile.tenant.cs_tenant_id,
        }
    }

    response = chirpstack_device_profile_get(device_profile)

    url = f"{CHIRPSTACK_DEVICE_PROFILE_URL}/{device_profile.cs_device_profile_id}"

    if response.status_code == 200:
        response = requests.put(url, json=payload, headers=HEADERS)
    elif (
        device_profile.cs_device_profile_id is None
        or device_profile.cs_device_profile_id == ""
    ):
        response = requests.post(
            CHIRPSTACK_DEVICE_PROFILE_URL, json=payload, headers=HEADERS
        )

    if response.status_code == 200:
        device_profile.sync_status = "SYNCED"
        device_profile.sync_error = ""
        device_profile.last_synced_at = dt.datetime.now()
        device_profile.save()
        logging.info(f"Updated device profile in Chirpstack: {device_profile.name}")
    else:
        device_profile.sync_status = "ERROR"
        device_profile.sync_error = response.text
        device_profile.last_synced_at = dt.datetime.now()
        device_profile.save()
        logging.error(
            f"Error updating device profile: {device_profile.name} \n {response.text}"
        )

    pass


def chirpstack_device_profile_destroy(device_profile):
    url = f"{CHIRPSTACK_DEVICE_PROFILE_URL}/{device_profile.cs_device_profile_id}"
    response = requests.delete(url, headers=HEADERS)
    if response.status_code == 200:
        logging.info(f"Deleted device profile in Chirpstack")
    else:
        logging.error(
            f"Error deleting device profile: Device Profile does not exist in Chirpstack or try to delete it manually."
        )
