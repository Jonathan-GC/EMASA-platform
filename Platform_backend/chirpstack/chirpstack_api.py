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


def sync_tenant_chirpstack(tenant, request):
    """
    Syncs a tenant with Chirpstack.

    Args:
        tenant (Tenant): a Tenant object
        request (HttpRequest): request object with method

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

    response = None

    if request.method == "GET":
        url = f"{CHIRPSTACK_TENANT_URL}/{tenant.cs_tenant_id}"
        response = requests.get(url, headers=HEADERS)

        if response.status_code == 200:
            data = response.json()["tenant"]

            changed = False
            for field, local_value in {
                "maxDeviceCount": tenant.subscription.max_device_count,
                "maxGatewayCount": tenant.subscription.max_gateway_count,
                "canHaveGateways": tenant.subscription.can_have_gateways,
                "description": tenant.description,
                "name": tenant.name,
            }.items():
                if data.get(field) != local_value:
                    payload["tenant"][field] = local_value
                    changed = True

            if changed:
                response = requests.put(url, json=payload, headers=HEADERS)

            tenant.sync_status = "SYNCED"
            if tenant.sync_error != "":
                tenant.sync_error = ""
            tenant.last_synced_at = dt.datetime.now()
            tenant.save()

            return response
        elif tenant.cs_tenant_id == "" or tenant.cs_tenant_id is None or tenant.cs_tenant_id != "":
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
                    response = requests.post(CHIRPSTACK_TENANT_URL, json=payload, headers=HEADERS)
        else:
            tenant.sync_status = "PENDING"
            tenant.sync_error = response.text
            tenant.last_synced_at = dt.datetime.now()
            tenant.save()
            return response

    elif request.method == "PUT":
        url = f"{CHIRPSTACK_TENANT_URL}/{tenant.cs_tenant_id}"
        if tenant.cs_tenant_id == "" or tenant.cs_tenant_id is None:
            response = requests.post(CHIRPSTACK_TENANT_URL, json=payload, headers=HEADERS)
        else:
            response = requests.put(url, json=payload, headers=HEADERS)

    elif request.method == "POST":
        response = requests.post(CHIRPSTACK_TENANT_URL, json=payload, headers=HEADERS)

    elif request.method == "DELETE":
        url = f"{CHIRPSTACK_TENANT_URL}/{tenant.cs_tenant_id}"
        response = requests.delete(url, headers=HEADERS)

    if response is not None and response.status_code == 200:
        if request.method == "POST":
            api_id = response.json()["id"]
            tenant.cs_tenant_id = api_id
        tenant.sync_status = "SYNCED"
        if tenant.sync_error != "":
                tenant.sync_error = ""
        tenant.last_synced_at = dt.datetime.now()   
        tenant.save()
    elif response is not None:
        tenant.sync_status = "ERROR"
        tenant.sync_error = response.text
        tenant.last_synced_at = dt.datetime.now()
        tenant.save()

    return response


def sync_gateway_chirpstack(gateway, request):
    """
    Syncs a gateway with Chirpstack.

    Args:
        gateway (Gateway): a Gateway object
        request (HttpRequest): request object with method

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

    response = None

    if request.method == "GET":
        response = requests.get(
            CHIRPSTACK_GATEWAYS_URL,
            headers=HEADERS,
            params={
                "tenant_id": gateway.workspace.tenant.cs_tenant_id,
                "limit": 100
            },
        )

        if response.status_code == 200:
            data = response.json().get("result", [])
            gw_data = next((g for g in data if g["gatewayId"] == gateway.cs_gateway_id), None)

            if gw_data:
                gateway.state = gw_data.get("state", gateway.state)
                gateway.last_seen_at = gw_data.get("lastSeenAt", gateway.last_seen_at)
                if gateway.sync_error!= "":
                    gateway.sync_error = ""
                gateway.sync_status = "SYNCED"
                gateway.last_synced_at = dt.datetime.now()
                gateway.save()
            else:
                # Missing gateway
                gateway.sync_status = "PENDING"
                gateway.sync_error = "Gateway not found in Chirpstack list"
                gateway.last_synced_at = dt.datetime.now()
                gateway.save()
        else:
            gateway.sync_status = "ERROR"
            gateway.sync_error = response.text
            gateway.last_synced_at = dt.datetime.now()
            gateway.save()

        return response

    elif request.method == "POST":
        response = requests.post(CHIRPSTACK_GATEWAYS_URL, json=payload, headers=HEADERS)
    
    elif request.method == "PUT":
        response = requests.put(
            f"{CHIRPSTACK_GATEWAYS_URL}/{gateway.cs_gateway_id}",
            json=payload,
            headers=HEADERS,
        )
        if response.status_code == 404:
            response = requests.post(CHIRPSTACK_GATEWAYS_URL, json=payload, headers=HEADERS)

    elif request.method == "DELETE":
        response = requests.delete(
            f"{CHIRPSTACK_GATEWAYS_URL}/{gateway.cs_gateway_id}",
            headers=HEADERS,
        )

    if response is not None and response.status_code == 200:
        gateway.sync_status = "SYNCED"
        if gateway.sync_error != "":
            gateway.sync_error = ""
        gateway.last_synced_at = dt.datetime.now()
        gateway.save()
    elif response is not None:
        gateway.sync_status = "ERROR"
        gateway.sync_error = response.text
        gateway.last_synced_at = dt.datetime.now()
        gateway.save()

    return response


def sync_api_user_chirpstack(api_user, request):
    """
    Syncs an API user with Chirpstack.

    Args:
        api_user (APIUser): an APIUser object
        method (str): one of "GET", "POST", "PUT", "DELETE"

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

    response = None

    if request.method == "GET":
        response = requests.get(
            CHIRPSTACK_API_URL,
            headers=HEADERS,
            params={"limit": 100},
        )

        if response.status_code == 200:
            results = response.json().get("result", [])
            match = next((u for u in results if u["email"] == api_user.email), None)

            if match:
                api_user.cs_user_id = match["id"]
                api_user.is_active = match.get("isActive", api_user.is_active)
                api_user.is_admin = match.get("isAdmin", api_user.is_admin)
                api_user.sync_status = "SYNCED"
                api_user.sync_error = ""
                api_user.last_synced_at = dt.datetime.now()
                api_user.save()
            else:
                if not api_user.cs_user_id or api_user.cs_user_id.strip() == "":
                    response = requests.post(CHIRPSTACK_API_URL, json=payload, headers=HEADERS)
                    if response.status_code == 200:
                        api_id = response.json()["id"]
                        api_user.cs_user_id = api_id
                        api_user.sync_status = "SYNCED"
                        api_user.sync_error = "User not found in Chirpstack but is created and synced now"
                        api_user.last_synced_at = dt.datetime.now()
                        api_user.save()
                else:
                    api_user.sync_status = "PENDING"
                    api_user.sync_error = "User not found in Chirpstack and cs_user_id is not empty"
                    api_user.last_synced_at = dt.datetime.now()
                    api_user.save()

        else:
            api_user.sync_status = "ERROR"
            api_user.sync_error = response.text
            api_user.last_synced_at = dt.datetime.now()
            api_user.save()

        return response

    elif request.method == "POST":
        response = requests.post(CHIRPSTACK_API_URL, json=payload, headers=HEADERS)

    elif request.method == "PUT":
        if not api_user.cs_user_id:
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

        if api_user.cs_user_id:
            url = f"{CHIRPSTACK_API_URL}/{api_user.cs_user_id}"
            response = requests.put(url, json=payload, headers=HEADERS)
        else:
            response = requests.post(CHIRPSTACK_API_URL, json=payload, headers=HEADERS)

    elif request.method == "DELETE":
        if api_user.cs_user_id:
            url = f"{CHIRPSTACK_API_URL}/{api_user.cs_user_id}"
            response = requests.delete(url, headers=HEADERS)

    if response is not None and response.status_code == 200:
        if request.method == "POST":
            api_id = response.json()["id"]
            api_user.cs_user_id = api_id
        api_user.sync_status = "SYNCED"
        api_user.sync_error = ""
        api_user.last_synced_at = dt.datetime.now()
        api_user.save()
    elif response is not None and request.method in ["POST", "PUT", "DELETE"]:
        api_user.sync_status = "ERROR"
        api_user.sync_error = response.text
        api_user.last_synced_at = dt.datetime.now()
        api_user.save()

    return response


def sync_device_profile_chirpstack(device_profile, request):
    """
    Syncs a DeviceProfile with Chirpstack.

    Args:
        device_profile (DeviceProfile): a DeviceProfile object
        request (HttpRequest): request containing method (GET, POST, PUT, DELETE)

    Returns:
        requests.Response: the response from Chirpstack API
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

    response = None

    if request.method == "GET":
        response = requests.get(
            CHIRPSTACK_DEVICE_PROFILE_URL,
            headers=HEADERS,
            params={"limit": 100},
        )

        if response.status_code == 200:
            results = response.json().get("result", [])
            match = next((d for d in results if d["name"] == device_profile.name), None)

            if match:
                dp_id = match["id"]
                detail_resp = requests.get(
                    f"{CHIRPSTACK_DEVICE_PROFILE_URL}/{dp_id}", headers=HEADERS
                )
                if detail_resp.status_code == 200:
                    detail = detail_resp.json()["deviceProfile"]

                    # sincroniza campos locales con ChirpStack
                    device_profile.cs_device_profile_id = dp_id
                    device_profile.name = detail["name"]
                    device_profile.description = detail.get("description", "")
                    device_profile.region = detail["region"]
                    device_profile.mac_version = detail["macVersion"]
                    device_profile.reg_param_revision = detail["regParamsRevision"]
                    device_profile.abp_rx1_delay = detail["abpRx1Delay"]
                    device_profile.abp_rx1_dr_offset = detail["abpRx1DrOffset"]
                    device_profile.abp_rx2_dr = detail["abpRx2Dr"]
                    device_profile.abp_rx2_freq = detail["abpRx2Freq"]
                    device_profile.is_relay = detail.get("isRelay", False)
                    device_profile.is_relay_ed = detail.get("isRelayEd", False)
                    device_profile.payload_codec_runtime = detail["payloadCodecRuntime"]
                    device_profile.payload_codec_script = detail.get("payloadCodecScript", "")

                    device_profile.sync_status = "SYNCED"
                    device_profile.sync_error = ""
                    device_profile.last_synced_at = dt.datetime.now()
                    device_profile.save()
                else:
                    # si falla el retrieve del detalle
                    device_profile.sync_status = "ERROR"
                    device_profile.sync_error = detail_resp.text
                    device_profile.last_synced_at = dt.datetime.now()
                    device_profile.save()
        else:
            device_profile.sync_status = "ERROR"
            device_profile.sync_error = response.text
            device_profile.last_synced_at = dt.datetime.now()
            device_profile.save()

        return response

    elif request.method == "POST":
        response = requests.post(CHIRPSTACK_DEVICE_PROFILE_URL, json=payload, headers=HEADERS)

    elif request.method == "PUT":
        if not device_profile.cs_device_profile_id:
            search_resp = requests.get(
                CHIRPSTACK_DEVICE_PROFILE_URL,
                headers=HEADERS,
                params={"limit": 100},
            )
            if search_resp.status_code == 200:
                results = search_resp.json().get("result", [])
                match = next((d for d in results if d["name"] == device_profile.name), None)
                if match:
                    device_profile.cs_device_profile_id = match["id"]
                    device_profile.save()

        if device_profile.cs_device_profile_id:
            url = f"{CHIRPSTACK_DEVICE_PROFILE_URL}/{device_profile.cs_device_profile_id}"
            response = requests.put(url, json=payload, headers=HEADERS)
        else:
            response = requests.post(CHIRPSTACK_DEVICE_PROFILE_URL, json=payload, headers=HEADERS)

    elif request.method == "DELETE":
        if device_profile.cs_device_profile_id:
            url = f"{CHIRPSTACK_DEVICE_PROFILE_URL}/{device_profile.cs_device_profile_id}"
            response = requests.delete(url, headers=HEADERS)

    if response is not None and response.status_code == 200:
        if request.method == "POST":
            api_id = response.json()["id"]
            device_profile.cs_device_profile_id = api_id
        device_profile.sync_status = "SYNCED"
        device_profile.sync_error = ""
        device_profile.last_synced_at = dt.datetime.now()
        device_profile.save()
    elif response is not None and request.method in ["POST", "PUT", "DELETE"]:
        device_profile.sync_status = "ERROR"
        device_profile.sync_error = response.text
        device_profile.last_synced_at = dt.datetime.now()
        device_profile.save()

    return response
