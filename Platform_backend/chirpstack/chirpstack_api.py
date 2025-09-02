import requests
from django.conf import settings
import datetime as dt

from organizations.models import Tenant, Subscription, Workspace
from infrastructure.models import Gateway, Location, Device, Application, Type, Machine
from chirpstack.models import ApiUser, DeviceProfile

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


def get_tenant_from_chirpstack():
    local_instances = Tenant.objects.all()

    list_response = requests.get(
        CHIRPSTACK_TENANT_URL, headers=HEADERS, params={"limit": 100}
    )
    if list_response.status_code == 200:
        cs_instance_list = list_response.json().get("result", [])
    else:
        cs_instance_list = []

    to_remove = []
    for instance in local_instances:
        match = next((t for t in cs_instance_list if t["name"] == instance.name), None)
        if match:
            to_remove.append(match)
            if instance.cs_tenant_id != match["id"]:
                instance.cs_tenant_id = match["id"]
            instance.sync_status = "SYNCED"
            instance.sync_error = ""
            instance.last_synced_at = dt.datetime.now()
            instance.save()
            logging.info(
                f"Tenant {instance.cs_tenant_id} - {instance.name} has been synced with Chirpstack"
            )
    for match in to_remove:
        cs_instance_list.remove(match)

    for new_instance in cs_instance_list:

        subscription, _ = Subscription.objects.get_or_create(
            max_gateway_count=int(new_instance.get("maxGatewayCount", 10)),
            defaults={
                "name": "Base",
                "description": "Base placeholder Subscription, please modify it",
                "can_have_gateways": new_instance.get("canHaveGateways", True),
                "max_device_count": new_instance.get("maxDeviceCount", 100),
            },
        )

        new_tenant = Tenant(
            cs_tenant_id=new_instance["id"],
            name=new_instance["name"],
            description=new_instance.get("description", ""),
            subscription=subscription,
            sync_status="SYNCED",
            sync_error="",
            last_synced_at=dt.datetime.now(),
        )
        new_tenant.save()
        logging.info(
            f"Tenant {new_tenant.cs_tenant_id} - {new_tenant.name} has been created from Chirpstack"
        )


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


def get_gateway_from_chirpstack():
    local_instances = Gateway.objects.all()
    list_response = requests.get(
        CHIRPSTACK_GATEWAYS_URL, headers=HEADERS, params={"limit": 100}
    )

    if list_response.status_code == 200:
        results = list_response.json().get("result", [])
        to_remove = []

        for item in results:
            match = next(
                (g for g in local_instances if g.cs_gateway_id == item["gatewayId"]),
                None,
            )
            if match:
                to_remove.append(item)
                match.state = item.get("state", match.state)
                match.last_seen_at = item.get("lastSeenAt", match.last_seen_at)
                match.sync_status = "SYNCED"
                match.sync_error = ""
                match.last_synced_at = dt.datetime.now()
                match.save()
                logging.info(
                    f"Gateway {match.cs_gateway_id} - {match.name} has been synced with Chirpstack"
                )
        for match in to_remove:
            results.remove(match)

        for new_instance in results:
            tenant = Tenant.objects.filter(
                cs_tenant_id=new_instance.get("tenantId")
            ).first()
            if tenant:
                workspace = tenant.workspace_set.first()
                if not workspace:
                    workspace = Workspace.objects.create(
                        name=f"{tenant.name} WS",
                        tenant=tenant,
                        description=f"{tenant.name}'s default workspace",
                    )
                    workspace.save()
                cs_location = new_instance.get("location", {})

                location = Location(
                    name=f"{new_instance['name']} Location",
                    accuracy=cs_location.get("accuracy", 0.0),
                    altitude=cs_location.get("altitude", 0.0),
                    latitude=cs_location.get("latitude", 0.0),
                    longitude=cs_location.get("longitude", 0.0),
                    source=cs_location.get("source", "UNKNOWN"),
                )
                location.save()
                new_gw = Gateway(
                    cs_gateway_id=new_instance["gatewayId"],
                    name=new_instance["name"],
                    description=new_instance.get("description", ""),
                    stats_interval=new_instance.get("statsInterval", 0),
                    state=new_instance.get("state", "unknown"),
                    last_seen_at=new_instance.get("lastSeenAt", None),
                    location=location,
                    workspace=workspace,
                    sync_status="SYNCED",
                    sync_error="",
                    last_synced_at=dt.datetime.now(),
                )
                new_gw.save()
                logging.info(
                    f"Gateway {new_gw.cs_gateway_id} - {new_gw.name} has been created from Chirpstack"
                )

            else:
                logging.warning(
                    f"No tenant found with cs_tenant_id {new_instance.get('tenantId')}. Gateway {new_instance['gatewayId']} was not created."
                )

    else:
        logging.error(f"Error fetching gateways from Chirpstack.")

    return list_response


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
    print(api_user.__dict__)
    payload = {
        "password": api_user.password,
        "tenants": [
            {
                "isAdmin": api_user.is_tenant_admin,
                "isDeviceAdmin": api_user.is_tenant_device_admin,
                "isGatewayAdmin": api_user.is_tenant_gateway_admin,
                "tenantId": api_user.workspace.tenant.cs_tenant_id,
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

    return response


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
                "tenantId": api_user.workspace.tenant.cs_tenant_id,
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
                "tenantId": api_user.workspace.tenant.cs_tenant_id,
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

    return response


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


def get_api_user_from_chirpstack():
    local_instances = ApiUser.objects.all()

    list_response = requests.get(
        CHIRPSTACK_API_URL,
        headers=HEADERS,
        params={"limit": 100},
    )
    print(list_response.status_code, list_response.text)
    if list_response.status_code == 200:
        users = list_response.json().get("result", [])
    else:
        users = []

    user_tenant_mapping = {}
    for tenant in Tenant.objects.exclude(cs_tenant_id__isnull=True):
        resp = requests.get(
            f"{CHIRPSTACK_API_URL}/tenants/{tenant.cs_tenant_id}/users",
            headers=HEADERS,
            params={"limit": 100},
        )
        if resp.status_code != 200:
            continue
        tenant_users = resp.json().get("result", [])
        for tu in tenant_users:
            uid = tu["userId"]
            if uid not in user_tenant_mapping:
                user_tenant_mapping[uid] = []
            user_tenant_mapping[uid].append(
                {
                    "tenant": tenant,
                    "isAdmin": tu.get("isAdmin", False),
                    "isDeviceAdmin": tu.get("isDeviceAdmin", False),
                    "isGatewayAdmin": tu.get("isGatewayAdmin", False),
                }
            )

    to_remove = []
    for instance in local_instances:
        match = next((u for u in users if u["email"] == instance.email), None)
        if match:
            to_remove.append(match)
            instance.cs_user_id = match["id"]
            instance.is_active = match.get("isActive", instance.is_active)
            instance.is_admin = match.get("isAdmin", instance.is_admin)
            instance.note = match.get("note", instance.note)
            instance.sync_status = "SYNCED"
            instance.sync_error = ""
            instance.last_synced_at = dt.datetime.now()

            for tinfo in user_tenant_mapping.get(instance.cs_user_id, []):
                workspace = tinfo["tenant"].workspace_set.first()
                instance.workspace = workspace
                instance.is_tenant_admin = tinfo["isAdmin"]
                instance.is_tenant_device_admin = tinfo["isDeviceAdmin"]
                instance.is_tenant_gateway_admin = tinfo["isGatewayAdmin"]

            instance.save()

    for new_instance in users:
        if ApiUser.objects.filter(email=new_instance["email"]).exists():
            continue

        tenant_info = user_tenant_mapping.get(new_instance["id"], [])
        workspace = (
            tenant_info[0]["tenant"].workspace_set.first() if tenant_info else None
        )

        api_user = ApiUser(
            email=new_instance["email"],
            cs_user_id=new_instance["id"],
            is_active=new_instance["isActive"],
            is_admin=new_instance["isAdmin"],
            note=new_instance.get("note", ""),
            workspace=workspace,
            password="",
            sync_error="Please set a new password",
            sync_status="SYNCED",
            last_synced_at=dt.datetime.now(),
        )

        if tenant_info:
            api_user.is_tenant_admin = tenant_info[0]["isAdmin"]
            api_user.is_tenant_device_admin = tenant_info[0]["isDeviceAdmin"]
            api_user.is_tenant_gateway_admin = tenant_info[0]["isGatewayAdmin"]

        api_user.save()

    return list_response


# DeviceProfile
def sync_device_profile_get(device_profile):
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
            "tenantId": device_profile.workspace.tenant.cs_tenant_id,
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


def sync_device_profile_create(device_profile):
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
            "tenantId": device_profile.workspace.tenant.cs_tenant_id,
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


def sync_device_profile_update(device_profile):
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
            "tenantId": device_profile.workspace.tenant.cs_tenant_id,
        }
    }

    response = sync_device_profile_get(device_profile)

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

    return response


def sync_device_profile_destroy(device_profile):
    url = f"{CHIRPSTACK_DEVICE_PROFILE_URL}/{device_profile.cs_device_profile_id}"
    response = requests.delete(url, headers=HEADERS)
    if response.status_code == 200:
        logging.info(f"Deleted device profile in Chirpstack")
    else:
        logging.error(
            f"Error deleting device profile: Device Profile does not exist in Chirpstack or try to delete it manually."
        )

    return response


def get_device_profiles_from_chirpstack():
    local_tenants = Tenant.objects.exclude(cs_tenant_id__isnull=True)
    for tenant in local_tenants:
        workspace = tenant.workspace_set.first()
        if not workspace:
            logging.warning(
                f"Tenant {tenant.name} does not have an associated workspace. Skipping..."
            )
            continue

        list_response = requests.get(
            CHIRPSTACK_DEVICE_PROFILE_URL,
            headers=HEADERS,
            params={"limit": 100, "tenantId": tenant.cs_tenant_id},
        )

        if list_response.status_code != 200:
            logging.error(
                f"Error fetching device profiles for tenant {tenant.cs_tenant_id}"
            )
            continue

        cs_profiles = list_response.json().get("result", [])
        local_profiles = DeviceProfile.objects.filter(workspace=workspace)

        to_remove = []
        for local_dp in local_profiles:
            match = next(
                (dp for dp in cs_profiles if dp["id"] == local_dp.cs_device_profile_id),
                None,
            )
            if match:
                to_remove.append(match)
                local_dp.name = match.get("name", local_dp.name)
                local_dp.region = match.get("region", local_dp.region)
                local_dp.mac_version = match.get("macVersion", local_dp.mac_version)
                local_dp.reg_param_revision = match.get(
                    "regParamsRevision", local_dp.reg_param_revision
                )
                local_dp.supports_otaa = match.get(
                    "supportsOtaa", local_dp.supports_otaa
                )
                local_dp.supports_class_b = match.get(
                    "supportsClassB", local_dp.supports_class_b
                )
                local_dp.supports_class_c = match.get(
                    "supportsClassC", local_dp.supports_class_c
                )
                local_dp.sync_status = "SYNCED"
                local_dp.sync_error = ""
                local_dp.last_synced_at = dt.datetime.now()
                local_dp.save()
                logging.info(
                    f"DeviceProfile {local_dp.cs_device_profile_id} - {local_dp.name} updated"
                )
        for match in to_remove:
            cs_profiles.remove(match)

        # crear los nuevos
        for new_dp in cs_profiles:
            dp = DeviceProfile(
                cs_device_profile_id=new_dp["id"],
                name=new_dp["name"],
                description="Imported from Chirpstack",
                region=new_dp.get("region", ""),
                workspace=workspace,
                mac_version=new_dp.get("macVersion", "LORAWAN_1_0_3"),
                reg_param_revision=new_dp.get("regParamsRevision", "A"),
                abp_rx1_delay=1,
                abp_rx1_dr_offset=0,
                abp_rx2_dr=0,
                abp_rx2_freq=0,
                supports_otaa=new_dp.get("supportsOtaa", False),
                supports_class_b=new_dp.get("supportsClassB", False),
                supports_class_c=new_dp.get("supportsClassC", False),
                sync_status="SYNCED",
                sync_error="",
                last_synced_at=dt.datetime.now(),
            )
            dp.save()
            logging.info(
                f"DeviceProfile {dp.cs_device_profile_id} - {dp.name} created from Chirpstack"
            )


# Application
def sync_application_create(application):
    payload = {
        "application": {
            "name": application.name,
            "description": application.description,
            "tenantId": application.workspace.tenant.cs_tenant_id,
        }
    }

    response = requests.post(CHIRPSTACK_APPLICATION_URL, json=payload, headers=HEADERS)

    if response.status_code == 200:
        application.cs_application_id = response.json()["id"]
        application.save()
        application.sync_status = "SYNCED"
        application.sync_error = ""
        application.last_synced_at = dt.datetime.now()
        application.save()
    else:
        application.sync_status = "ERROR"
        application.sync_error = response.text
        application.last_synced_at = dt.datetime.now()
        application.save()
    return response


def sync_application_get(application):
    payload = {
        "application": {
            "name": application.name,
            "description": application.description,
            "tenantId": application.workspace.tenant.cs_tenant_id,
        }
    }

    url = f"{CHIRPSTACK_APPLICATION_URL}/{application.cs_application_id}"
    response = requests.get(url, headers=HEADERS)

    logging.info(f"Get response: {response.status_code}, {response.json()}")

    if response.status_code == 200:
        logging.info(f"Found application in chirpstack: {application.name}")
        application.cs_application_id = response.json()["application"]["id"]
        application.sync_status = "SYNCED"
        if application.sync_error != "":
            application.sync_error = ""
        application.last_synced_at = dt.datetime.now()
        application.save()
    elif application.cs_application_id == "" or application.cs_application_id is None:
        list_response = requests.get(
            CHIRPSTACK_APPLICATION_URL,
            headers=HEADERS,
            params={
                "limit": 100,
                "tenantId": application.workspace.tenant.cs_tenant_id,
            },
        )
        logging.info(
            f"List response: {list_response.status_code}, {list_response.json()}"
        )
        if list_response.status_code == 200:
            results = list_response.json().get("result", [])
            match = next((a for a in results if a["name"] == application.name), None)
            if match:
                application.cs_application_id = match["id"]
                application.sync_status = "SYNCED"
                if application.sync_error != "":
                    application.sync_error = ""
                application.last_synced_at = dt.datetime.now()
                application.save()
                return list_response
            else:
                response = sync_application_create(application)
    else:
        application.sync_status = "ERROR"
        application.sync_error = response.text
        application.last_synced_at = dt.datetime.now()
        application.save()

    return response


def sync_application_update(application):
    payload = {
        "application": {
            "name": application.name,
            "description": application.description,
            "tenantId": application.workspace.tenant.cs_tenant_id,
        }
    }

    url = f"{CHIRPSTACK_APPLICATION_URL}/{application.cs_application_id}"

    response = sync_application_get(application)

    if response.status_code == 200:
        response = requests.put(url, json=payload, headers=HEADERS)
    elif application.cs_application_id is None or application.cs_application_id == "":
        response = sync_application_create(application)

    if response.status_code == 200:
        application.sync_status = "SYNCED"
        application.sync_error = ""
        application.last_synced_at = dt.datetime.now()
        application.save()
    else:
        application.sync_status = "ERROR"
        application.sync_error = response.text
        application.last_synced_at = dt.datetime.now()
        application.save()

    return response


def sync_application_destroy(application):
    url = f"{CHIRPSTACK_APPLICATION_URL}/{application.cs_application_id}"
    response = requests.delete(url, headers=HEADERS)
    if response.status_code == 200:
        logging.info(f"Deleted application in Chirpstack")
    else:
        logging.error(
            f"Error deleting application: Application does not exist in Chirpstack or try to delete it manually."
        )

    return response


def get_applications_from_chirpstack():
    local_tenants = Tenant.objects.exclude(cs_tenant_id__isnull=True)

    for tenant in local_tenants:
        workspace = tenant.workspace_set.first()
        if not workspace:
            logging.warning(
                f"Tenant {tenant.name} does not have an associated workspace. Skipping..."
            )
            continue

        list_response = requests.get(
            CHIRPSTACK_APPLICATION_URL,
            headers=HEADERS,
            params={"limit": 100, "tenantId": tenant.cs_tenant_id},
        )

        if list_response.status_code != 200:
            logging.error(
                f"Error fetching applications for tenant {tenant.cs_tenant_id}"
            )
            continue

        cs_apps = list_response.json().get("result", [])
        local_apps = Application.objects.filter(workspace=workspace)

        to_remove = []
        for local_app in local_apps:
            match = next(
                (a for a in cs_apps if a["id"] == local_app.cs_application_id), None
            )
            if match:
                to_remove.append(match)
                # actualizar campos
                local_app.name = match.get("name", local_app.name)
                local_app.description = match.get("description", local_app.description)
                local_app.sync_status = "SYNCED"
                local_app.sync_error = ""
                local_app.last_synced_at = dt.datetime.now()
                local_app.save()
                logging.info(
                    f"Application {local_app.cs_application_id} - {local_app.name} updated"
                )

        for match in to_remove:
            cs_apps.remove(match)

        # obtener un Type genérico si no existe relación explícita
        default_type, _ = Type.objects.get_or_create(
            name="Generic", defaults={"description": "Generic device type"}
        )

        # crear los nuevos
        for new_app in cs_apps:
            app = Application(
                cs_application_id=new_app["id"],
                name=new_app.get("name", ""),
                description=new_app.get("description", ""),
                workspace=workspace,
                device_type=default_type,
                sync_status="SYNCED",
                sync_error="",
                last_synced_at=dt.datetime.now(),
            )
            app.save()
            logging.info(
                f"Application {app.cs_application_id} - {app.name} created from Chirpstack"
            )


# Device
def sync_device_create(device):
    payload = {
        "device": {
            "devEui": device.dev_eui,
            "name": device.name,
            "applicationId": device.application.cs_application_id,
            "description": device.description,
            "deviceProfileId": device.device_profile.cs_device_profile_id,
            "isDisabled": device.is_disabled,
        }
    }

    response = requests.post(CHIRPSTACK_DEVICE_URL, json=payload, headers=HEADERS)

    if response.status_code == 200:
        device.sync_status = "SYNCED"
        if device.sync_error != "":
            device.sync_error = ""
        device.last_synced_at = dt.datetime.now()
        device.save()
    else:
        device.sync_status = "ERROR"
        device.sync_error = response.text
        device.last_synced_at = dt.datetime.now()
        device.save()

    return response


def sync_device_get(device):
    payload = {
        "device": {
            "devEui": device.dev_eui,
            "name": device.name,
            "applicationId": device.application.cs_application_id,
            "description": device.description,
            "deviceProfileId": device.device_profile.cs_device_profile_id,
            "isDisabled": device.is_disabled,
        }
    }

    url = f"{CHIRPSTACK_DEVICE_URL}/{device.dev_eui}"
    response = requests.get(url, headers=HEADERS)
    print(response.status_code, response.json())

    if response.status_code == 200:
        logging.info(f"Found device in chirpstack: {device.name}")
        device.sync_status = "SYNCED"
        if device.sync_error != "":
            device.sync_error = ""
        device.last_synced_at = dt.datetime.now()
        device.save()
    elif device.dev_eui:
        response = sync_device_create(device)
    else:
        device.sync_status = "ERROR"
        device.sync_error = response.text
        device.last_synced_at = dt.datetime.now()
        device.save()

    return response


def sync_device_update(device):
    payload = {
        "device": {
            "devEui": device.dev_eui,
            "name": device.name,
            "applicationId": device.application.cs_application_id,
            "description": device.description,
            "deviceProfileId": device.device_profile.cs_device_profile_id,
            "isDisabled": device.is_disabled,
        }
    }

    url = f"{CHIRPSTACK_DEVICE_URL}/{device.dev_eui}"

    response = sync_device_get(device)

    if response.status_code == 200:
        response = requests.put(url, json=payload, headers=HEADERS)
    elif device.dev_eui:
        response = sync_device_create(device)

    if response.status_code == 200:
        device.sync_status = "SYNCED"
        device.sync_error = ""
        device.last_synced_at = dt.datetime.now()
        device.save()
    else:
        device.sync_status = "ERROR"
        device.sync_error = response.text
        device.last_synced_at = dt.datetime.now()
        device.save()

    return response


def sync_device_destroy(device):
    url = f"{CHIRPSTACK_DEVICE_URL}/{device.dev_eui}"
    response = requests.delete(url, headers=HEADERS)
    if response.status_code == 200:
        logging.info(f"Deleted device in Chirpstack")
    else:
        logging.error(
            f"Error deleting device: Device does not exist in Chirpstack or try to delete it manually."
        )

    return response


def activate_device(device):
    payload = {
        "deviceActivation": {
            "aFCntDown": device.activation.afcntdown,
            "appSKey": device.activation.app_s_key,
            "devAddr": device.activation.dev_addr,
            "fCntUp": device.activation.f_cnt_up,
            "fNwkSIntKey": device.activation.f_nwk_s_int_key,
            "nFCntDown": device.activation.n_f_cnt_down,
            "nwkSEncKey": device.activation.nwk_s_enc_key,
        }
    }
    url = f"{CHIRPSTACK_DEVICE_URL}/{device.dev_eui}/activate"
    response = requests.post(url, json=payload, headers=HEADERS)
    return response


def deactivate_device(device):
    url = f"{CHIRPSTACK_DEVICE_URL}/{device.dev_eui}/activation"
    response = requests.delete(url, headers=HEADERS)
    return response


def get_devices_from_chirpstack():
    local_apps = Application.objects.exclude(cs_application_id__isnull=True)

    for app in local_apps:
        workspace = app.workspace
        list_response = requests.get(
            CHIRPSTACK_DEVICE_URL,
            headers=HEADERS,
            params={"limit": 100, "applicationId": app.cs_application_id},
        )

        if list_response.status_code != 200:
            logging.error(
                f"Error fetching devices for application {app.cs_application_id}"
            )
            continue

        cs_devices = list_response.json().get("result", [])
        local_devices = Device.objects.filter(application=app)

        to_remove = []
        for local_dev in local_devices:
            match = next(
                (d for d in cs_devices if d["devEui"] == local_dev.dev_eui), None
            )
            if match:
                to_remove.append(match)

                try:
                    dp = DeviceProfile.objects.get(
                        cs_device_profile_id=match["deviceProfileId"]
                    )
                except DeviceProfile.DoesNotExist:
                    logging.warning(
                        f"DeviceProfile {match['deviceProfileId']} not found for device {match['devEui']}"
                    )
                    dp = None

                local_dev.name = match.get("name", local_dev.name)
                local_dev.description = match.get("description", local_dev.description)
                local_dev.device_profile = dp if dp else local_dev.device_profile
                local_dev.last_seen_at = match.get("lastSeenAt")
                local_dev.sync_status = "SYNCED"
                local_dev.sync_error = ""
                local_dev.last_synced_at = dt.datetime.now()
                local_dev.save()
                logging.info(f"Device {local_dev.dev_eui} updated")

        for match in to_remove:
            cs_devices.remove(match)

        default_type, _ = Type.objects.get_or_create(
            name="Generic", defaults={"description": "Generic type"}
        )
        default_machine, _ = Machine.objects.get_or_create(
            name="Generic Machine",
            workspace=workspace,
            defaults={"description": "Default machine"},
        )

        for new_dev in cs_devices:
            try:
                dp = DeviceProfile.objects.get(
                    cs_device_profile_id=new_dev["deviceProfileId"]
                )
            except DeviceProfile.DoesNotExist:
                dp = None

            dev = Device(
                dev_eui=new_dev["devEui"],
                name=new_dev.get("name", ""),
                description=new_dev.get("description", ""),
                application=app,
                workspace=workspace,
                machine=default_machine,
                device_type=default_type,
                device_profile=dp,
                is_disabled=False,
                last_seen_at=new_dev.get("lastSeenAt"),
                sync_status="SYNCED",
                sync_error="",
                last_synced_at=dt.datetime.now(),
            )
            dev.save()
            logging.info(f"Device {dev.dev_eui} - {dev.name} created from Chirpstack")
