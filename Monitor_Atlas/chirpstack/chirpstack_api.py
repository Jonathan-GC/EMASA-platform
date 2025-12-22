import requests
from django.conf import settings
import datetime as dt

from organizations.models import Tenant, Workspace
from infrastructure.models import Gateway, Location, Device, Application, Type, Machine
from chirpstack.models import ApiUser, DeviceProfile

from organizations.helpers import (
    get_or_create_default_workspace,
    get_or_create_default_subscription,
)

from .helpers import (
    fetch_chirpstack_users,
    fetch_tenant_user_mapping,
    update_existing_user,
    create_new_user,
    fetch_device_profiles,
    update_local_device_profile,
    create_local_device_profile,
    fetch_applications,
    update_local_application,
    create_local_application,
    fetch_devices,
    update_local_device,
    create_local_device,
)

from loguru import logger

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


# Local actions
def error_syncing(instance, response):
    instance.sync_status = "ERROR"
    instance.sync_error = response.text
    instance.last_synced_at = dt.datetime.now()
    instance.save(update_fields=["sync_status", "sync_error", "last_synced_at"])
    logger.error(f"Error syncing {instance}: {response.text}")


def set_status(instance, response):
    if response is None:
        logger.debug(f"No changes made to {instance} in chirpstack")
        return
    if response and response.status_code == 200:
        instance.sync_status = "SYNCED"
        instance.sync_error = ""
        instance.last_synced_at = dt.datetime.now()
        instance.save(update_fields=["sync_status", "sync_error", "last_synced_at"])
        logger.debug(f"{instance} synced successfully")
    else:
        error_syncing(instance, response)


# Helpers
def test_connection():
    try:
        response = requests.get(CHIRPSTACK_API_URL, headers=HEADERS, timeout=10)
        if response and response.status_code == 200:
            logger.debug("Connection to ChirpStack successful.")
            return True
        else:
            logger.error(
                f"Failed to connect to ChirpStack. Status code: {response.status_code}, Response: {response.text}"
            )
            return False
    except requests.exceptions.Timeout:
        logger.error(
            f"Timeout connecting to ChirpStack. The server took too long to respond."
        )
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Error connecting to ChirpStack: {e}")
        return False


# Tenants
def has_tenant_id(tenant):
    return tenant.cs_tenant_id is not None and tenant.cs_tenant_id != ""


def get_tenant_by_id(tenant):
    found = False
    if has_tenant_id(tenant):
        response = requests.get(
            f"{CHIRPSTACK_TENANT_URL}/{tenant.cs_tenant_id}",
            headers=HEADERS,
        )
        if response and response.status_code == 200:
            found = True
    return found


def create_tenant_in_chirpstack(tenant):
    payload = {
        "tenant": {
            "name": tenant.name,
            "description": tenant.description,
            "canHaveGateways": tenant.subscription.can_have_gateways,
            "maxDeviceCount": tenant.subscription.max_device_count,
            "maxGatewayCount": tenant.subscription.max_gateway_count,
        }
    }

    if not has_tenant_id(tenant):
        search_instance = requests.get(
            CHIRPSTACK_TENANT_URL,
            headers=HEADERS,
            params={"limit": 100},
        )
        if search_instance.status_code == 200:
            results = search_instance.json().get("result", [])
            match = next((t for t in results if t["name"] == tenant.name), None)
            if match:
                tenant.cs_tenant_id = match["id"]
                tenant.save(update_fields=["cs_tenant_id"])
                set_status(tenant, search_instance)
                return search_instance
            else:
                response = requests.post(
                    CHIRPSTACK_TENANT_URL, json=payload, headers=HEADERS
                )
                if response and response.status_code == 200:
                    tenant_data = response.json()
                    tenant.cs_tenant_id = tenant_data.get("id")
                    tenant.save(update_fields=["cs_tenant_id"])
                set_status(tenant, response)
                return response
    else:
        found = get_tenant_by_id(tenant)
        if not found:
            response = requests.post(
                CHIRPSTACK_TENANT_URL, json=payload, headers=HEADERS
            )
            if response and response.status_code == 200:
                tenant_data = response.json()
                tenant.cs_tenant_id = tenant_data.get("id")
                tenant.save(update_fields=["cs_tenant_id"])
            set_status(tenant, response)
            return response


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
    tenant_id = has_tenant_id(tenant)

    response = None

    if tenant_id:
        cs_tenant_id = tenant.cs_tenant_id
        url = f"{CHIRPSTACK_TENANT_URL}/{cs_tenant_id}"
        response = requests.get(url, headers=HEADERS)
    else:
        response = create_tenant_in_chirpstack(tenant)

    set_status(tenant, response)

    return response


def sync_tenant_create(tenant):
    """
    Syncs a tenant with Chirpstack.

    Args:
        tenant (Tenant): a Tenant object

    Returns:
        requests.Response: the response from the API
    """
    response = create_tenant_in_chirpstack(tenant)
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

    if response and response.status_code == 200:
        response = requests.put(url, json=payload, headers=HEADERS)

    set_status(tenant, response)

    return response


def sync_tenant_destroy(tenant):
    """
    Deletes a tenant in Chirpstack.

    Args:
        tenant (Tenant): a Tenant object

    Returns:
        requests.Response: the response from the API
    """
    response = None
    if has_tenant_id(tenant) and get_tenant_by_id(tenant):
        response = requests.delete(
            f"{CHIRPSTACK_TENANT_URL}/{tenant.cs_tenant_id}",
            headers=HEADERS,
        )

        if response and response.status_code == 200:
            logger.debug(f"Tenant deleted in Chirpstack")
            return response

        logger.error(f"Error deleting tenant try to delete it manually.")

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

    to_remove_ids = []
    for instance in local_instances:
        match = next((t for t in cs_instance_list if t["name"] == instance.name), None)
        if match:
            to_remove_ids.append(match["id"])
            if instance.cs_tenant_id != match["id"]:
                instance.cs_tenant_id = match["id"]
            instance.sync_status = "SYNCED"
            instance.sync_error = ""
            instance.last_synced_at = dt.datetime.now()
            instance.save()
            logger.debug(
                f"Tenant {instance.cs_tenant_id} - {instance.name} has been synced with Chirpstack"
            )

    # remover los que ya están sincronizados, por id
    cs_instance_list = [t for t in cs_instance_list if t["id"] not in to_remove_ids]

    # crear los que faltan en local
    for new_instance in cs_instance_list:
        subscription = get_or_create_default_subscription()
        new_tenant = Tenant(
            cs_tenant_id=new_instance["id"],
            name=new_instance["name"],
            description=new_instance.get(
                "description", f"{new_instance['name']}: synced tenant"
            ),
            subscription=subscription,
            sync_status="SYNCED",
            sync_error="",
            last_synced_at=dt.datetime.now(),
        )
        new_tenant.save()
        workspace = get_or_create_default_workspace(new_tenant)
        logger.debug(
            f"Tenant {new_tenant.cs_tenant_id} - {new_tenant.name} with its default workspace {workspace.id} has been created from Chirpstack"
        )
    return list_response


# Gateways
def get_gateway_by_id(gateway):
    found = False
    response = requests.get(
        f"{CHIRPSTACK_GATEWAYS_URL}/{gateway.cs_gateway_id}",
        headers=HEADERS,
    )
    if response and response.status_code == 200:
        found = True
    return found


def create_gateway_in_chirpstack(gateway):
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

    found = get_gateway_by_id(gateway)
    if not found:
        response = requests.post(CHIRPSTACK_GATEWAYS_URL, json=payload, headers=HEADERS)
        set_status(gateway, response)
        return response
    return None


def sync_gateway_status(gateway):
    response = requests.get(
        CHIRPSTACK_GATEWAYS_URL,
        headers=HEADERS,
        params={"tenantId": gateway.workspace.tenant.cs_tenant_id, "limit": 100},
    )
    if response and response.status_code == 200:
        results = response.json().get("result", [])
        match = next(
            (g for g in results if g["gatewayId"] == gateway.cs_gateway_id), None
        )
        if match:
            gateway.state = match.get("state", gateway.state)
            gateway.last_seen_at = match.get("lastSeenAt", gateway.last_seen_at)
        else:
            logger.warning(f"Gateway {gateway.cs_gateway_id} not found in Chirpstack.")
        gateway.save(update_fields=["state", "last_seen_at"])
        set_status(gateway, response)
    return response


def sync_gateway_get(gateway):
    response = create_gateway_in_chirpstack(gateway)

    status_response = sync_gateway_status(gateway)

    if status_response is not None:
        response = status_response

    set_status(gateway, response)
    return response


def sync_gateway_create(gateway):
    response = create_gateway_in_chirpstack(gateway)

    if response is not None and response.status_code == 200:
        response = sync_gateway_status(gateway)

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
    logger.debug(
        f"Updating gateway {gateway.cs_gateway_id} in Chirpstack. Payload: {payload}"
    )
    found = get_gateway_by_id(gateway)

    if found:
        response = requests.put(
            f"{CHIRPSTACK_GATEWAYS_URL}/{gateway.cs_gateway_id}",
            json=payload,
            headers=HEADERS,
        )
    else:
        response = create_gateway_in_chirpstack(gateway)
    set_status(gateway, response)
    return response


def sync_gateway_destroy(gateway):
    found = get_gateway_by_id(gateway)
    if found:
        response = requests.delete(
            f"{CHIRPSTACK_GATEWAYS_URL}/{gateway.cs_gateway_id}",
            headers=HEADERS,
        )
        if response and response.status_code == 200:
            logger.debug(f"Gateway deleted in Chirpstack")
            return response

        logger.error(f"Error deleting gateway try to delete it manually.")
        return response
    return None


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
                logger.debug(
                    f"Gateway {match.cs_gateway_id} - {match.name} has been synced with Chirpstack"
                )
        for match in to_remove:
            results.remove(match)

        for new_instance in results:
            tenant = Tenant.objects.filter(
                cs_tenant_id=new_instance.get("tenantId")
            ).first()
            if tenant:
                workspace = get_or_create_default_workspace(tenant)
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
                logger.debug(
                    f"Gateway {new_gw.cs_gateway_id} - {new_gw.name} has been created from Chirpstack"
                )

            else:
                logger.warning(
                    f"No tenant found with cs_tenant_id {new_instance.get('tenantId')}. Gateway {new_instance['gatewayId']} was not created."
                )

    else:
        logger.error(f"Error fetching gateways from Chirpstack.")

    return list_response


# Chirpstack user
def has_user_id(api_user):
    return api_user.cs_user_id is not None and api_user.cs_user_id != ""


def get_api_user_by_id(api_user):
    found = False
    if has_user_id(api_user):
        response = requests.get(
            f"{CHIRPSTACK_API_URL}/{api_user.cs_user_id}",
            headers=HEADERS,
        )
        if response and response.status_code == 200:
            found = True
    return found


def create_api_user_in_chirpstack(api_user):
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

    if not has_user_id(api_user):
        search_instance = requests.get(
            CHIRPSTACK_API_URL,
            headers=HEADERS,
            params={"limit": 100},
        )
        if search_instance.status_code == 200:
            results = search_instance.json().get("result", [])
            match = next((u for u in results if u["email"] == api_user.email), None)
            if match:
                api_user.cs_user_id = match["id"]
                api_user.save(update_fields=["cs_user_id"])
                set_status(api_user, search_instance)
                return search_instance
            else:
                response = requests.post(
                    CHIRPSTACK_API_URL, json=payload, headers=HEADERS
                )
                set_status(api_user, response)
                return response


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
    user_id = has_user_id(api_user)

    response = None

    if user_id:
        cs_user_id = api_user.cs_user_id
        response = requests.get(
            f"{CHIRPSTACK_API_URL}/{cs_user_id}",
            headers=HEADERS,
        )
    else:
        response = create_api_user_in_chirpstack(api_user)

    set_status(api_user, response)

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

    response = create_api_user_in_chirpstack(api_user)
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

    response = sync_api_user_get(api_user)

    url = f"{CHIRPSTACK_API_URL}/{api_user.cs_user_id}"

    if response and response.status_code == 200:
        response = requests.put(url, json=payload, headers=HEADERS)

    set_status(api_user, response)

    return response


def sync_api_user_destroy(api_user):
    """
    Syncs a DeviceProfile with Chirpstack.

    Args:
        api_user (ApiUser): an ApiUser object

    Returns:
        requests.Response: the response from the API
    """
    response = None

    if has_user_id(api_user) and get_api_user_by_id(api_user):
        response = requests.delete(
            f"{CHIRPSTACK_API_URL}/{api_user.cs_user_id}",
            headers=HEADERS,
        )

        if response and response.status_code == 200:
            logger.debug(f"API User deleted in Chirpstack")
            return response

        logger.error(f"Error deleting API User try to delete it manually.")

    return response


def get_api_user_from_chirpstack():
    """
    Syncs API users from Chirpstack to the local database.
    Updates existing users and creates new users when necessary.
    """
    local_instances = ApiUser.objects.all()

    users, list_response = fetch_chirpstack_users(CHIRPSTACK_API_URL, HEADERS)

    user_tenant_mapping = fetch_tenant_user_mapping(
        Tenant.objects.exclude(cs_tenant_id__isnull=True),
        CHIRPSTACK_TENANT_URL,
        HEADERS,
    )

    users_by_email = {u["email"]: u for u in users}

    for instance in local_instances:
        match = users_by_email.get(instance.email)
        if match:
            update_existing_user(instance, match, user_tenant_mapping)

    for new_instance in users:
        create_new_user(new_instance, user_tenant_mapping)

    return list_response


# DeviceProfile
def has_device_profile_id(device_profile):
    return (
        device_profile.cs_device_profile_id is not None
        and device_profile.cs_device_profile_id != ""
    )


def get_device_profile_by_id(device_profile):
    found = False
    if has_device_profile_id(device_profile):
        response = requests.get(
            f"{CHIRPSTACK_DEVICE_PROFILE_URL}/{device_profile.cs_device_profile_id}",
            headers=HEADERS,
        )
        if response and response.status_code == 200:
            found = True
    return found


def create_device_profile_in_chirpstack(device_profile):
    """
    Creates a device profile in Chirpstack, ensuring no duplicates by name.
    """
    exists = check_existing_device_profile(device_profile)
    if exists:
        logger.info(
            f"Device profile with name '{device_profile.name}' already exists in Chirpstack. Skipping creation."
        )
        return None

    payload = {
        "deviceProfile": {
            "name": device_profile.name,
            "description": device_profile.description,
            "region": device_profile.region,
            "macVersion": device_profile.mac_version,
            "regParamsRevision": device_profile.reg_param_revision,
            "supportsOtaa": device_profile.supports_otaa,
            "adrAlgorithmId": device_profile.adr_algorithm_id,
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
            "flushQueueOnActivate": device_profile.flush_queue_on_activate,
            "uplinkInterval": device_profile.uplink_interval,
        }
    }

    response = requests.post(
        CHIRPSTACK_DEVICE_PROFILE_URL, json=payload, headers=HEADERS
    )

    if response and response.status_code == 200:
        device_profile_data = response.json()
        device_profile.cs_device_profile_id = device_profile_data.get("id")
        device_profile.save(update_fields=["cs_device_profile_id"])
        logger.info(f"Created new device profile: {device_profile.name}")

    set_status(device_profile, response)

    return response


def check_existing_device_profile(new_dp):
    """
    Check if a device profile with the same name exists in Chirpstack and update new_dp.cs_device_profile_id in place.

    This function mutates the new_dp object by setting its cs_device_profile_id if a match is found.
    Returns True if an existing device profile is found, otherwise False.
    """

    # Reset cs_device_profile_id to avoid using a stale value from previous runs
    new_dp.cs_device_profile_id = None

    search_response = requests.get(
        CHIRPSTACK_DEVICE_PROFILE_URL,
        headers=HEADERS,
        params={
            "limit": 100,
            "tenantId": new_dp.workspace.tenant.cs_tenant_id,
        },
    )
    if search_response.status_code == 200:
        results = search_response.json().get("result", [])
        match = next((dp for dp in results if dp["name"] == new_dp.name), None)

        if match:
            new_dp.cs_device_profile_id = match["id"]
            new_dp.save(update_fields=["cs_device_profile_id"])
            set_status(new_dp, search_response)
            logger.info(
                f"Using existing device profile: {match['name']} (ID: {match['id']})"
            )
            if new_dp.cs_device_profile_id:
                found = get_device_profile_by_id(new_dp)
                if not found:
                    logger.warning(
                        f"Device profile {new_dp.name} has ID {new_dp.cs_device_profile_id} "
                        f"but doesn't exist in Chirpstack. Clearing ID."
                    )
                    new_dp.cs_device_profile_id = None
                    new_dp.save(update_fields=["cs_device_profile_id"])
                    return False
            return True
        else:
            logger.info(f"No existing device profile found for: {new_dp.name}")
    return False


def sync_device_profile_get(device_profile):
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
    device_profile_id = has_device_profile_id(device_profile)

    response = None

    if device_profile_id:
        cs_device_profile_id = device_profile.cs_device_profile_id
        response = requests.get(
            f"{CHIRPSTACK_DEVICE_PROFILE_URL}/{cs_device_profile_id}",
            headers=HEADERS,
        )
    else:
        response = create_device_profile_in_chirpstack(device_profile)

    set_status(device_profile, response)

    return response


def sync_device_profile_create(device_profile):
    """
    Syncs a DeviceProfile with Chirpstack.

    Args:
        device_profile (DeviceProfile): a DeviceProfile object

    Returns:
        requests.Response: the response from the API

    Side Effects:
        Updates device_profile fields such as cs_device_profile_id, sync_status, sync_error, and last_synced_at.
    """

    response = create_device_profile_in_chirpstack(device_profile)
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
            "adrAlgorithmId": device_profile.adr_algorithm_id,
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
            "flushQueueOnActivate": device_profile.flush_queue_on_activate,
            "uplinkInterval": device_profile.uplink_interval,
        }
    }

    url = f"{CHIRPSTACK_DEVICE_PROFILE_URL}/{device_profile.cs_device_profile_id}"

    response = sync_device_profile_get(device_profile)

    if response and response.status_code == 200:
        response = requests.put(url, json=payload, headers=HEADERS)

    set_status(device_profile, response)

    return response


def sync_device_profile_destroy(device_profile):
    response = None
    if has_device_profile_id(device_profile) and get_device_profile_by_id(
        device_profile
    ):
        response = requests.delete(
            f"{CHIRPSTACK_DEVICE_PROFILE_URL}/{device_profile.cs_device_profile_id}",
            headers=HEADERS,
        )

        if response and response.status_code == 200:
            logger.debug(f"DeviceProfile deleted in Chirpstack")
            return response

        logger.error(f"Error deleting DeviceProfile try to delete it manually.")

    return response


def get_device_profiles_from_chirpstack():
    """Sync device profiles from Chirpstack to local DB per tenant."""
    local_tenants = Tenant.objects.exclude(cs_tenant_id__isnull=True)
    last_response = None

    for tenant in local_tenants:
        workspace = get_or_create_default_workspace(tenant)
        if not workspace:
            logger.warning(
                f"Tenant {tenant.name} does not have an associated workspace. Skipping..."
            )
            continue

        cs_profiles, response = fetch_device_profiles(
            tenant, CHIRPSTACK_DEVICE_PROFILE_URL, HEADERS
        )
        last_response = response

        local_profiles = DeviceProfile.objects.filter(workspace=workspace)
        to_remove = []

        for local_dp in local_profiles:
            match = next(
                (dp for dp in cs_profiles if dp["id"] == local_dp.cs_device_profile_id),
                None,
            )
            if match:
                to_remove.append(match)
                update_local_device_profile(local_dp, match, workspace)

        for match in to_remove:
            cs_profiles.remove(match)

        for new_dp in cs_profiles:
            create_local_device_profile(new_dp, workspace)

    return last_response


# Application
def has_application_id(application):
    return (
        application.cs_application_id is not None
        and application.cs_application_id != ""
    )


def get_application_by_id(application):
    found = False
    if has_application_id(application):
        response = requests.get(
            f"{CHIRPSTACK_APPLICATION_URL}/{application.cs_application_id}",
            headers=HEADERS,
        )
        if response and response.status_code == 200:
            found = True
    return found


def create_application_in_chirpstack(application):
    payload = {
        "application": {
            "name": application.name,
            "description": application.description,
            "tenantId": application.workspace.tenant.cs_tenant_id,
        }
    }

    found = get_application_by_id(application)
    if not found:
        search_instance = requests.get(
            CHIRPSTACK_APPLICATION_URL,
            headers=HEADERS,
            params={
                "limit": 100,
                "tenantId": application.workspace.tenant.cs_tenant_id,
            },
        )
        if search_instance.status_code == 200:
            results = search_instance.json().get("result", [])
            match = next((a for a in results if a["name"] == application.name), None)
            if match:
                application.cs_application_id = match["id"]
                application.save(update_fields=["cs_application_id"])
                set_status(application, search_instance)
                return search_instance
            else:
                logger.debug(
                    f"Application not found. Creating application {application.name} in Chirpstack."
                )
                response = requests.post(
                    CHIRPSTACK_APPLICATION_URL, json=payload, headers=HEADERS
                )
                if response and response.status_code == 200:
                    application_data = response.json()
                    application.cs_application_id = application_data.get("id")
                    application.save(update_fields=["cs_application_id"])
                set_status(application, response)
                return response
    return None


def sync_application_create(application):
    response = create_application_in_chirpstack(application)
    return response


def sync_application_get(application):

    application_id = has_application_id(application)

    response = None

    if application_id:
        cs_application_id = application.cs_application_id
        response = requests.get(
            f"{CHIRPSTACK_APPLICATION_URL}/{cs_application_id}",
            headers=HEADERS,
        )
        if response.status_code != 200:
            logger.debug(
                f"Application ID {cs_application_id} not found in Chirpstack. Attempting to create. Response: {response.text}"
            )
            response = create_application_in_chirpstack(application)
    else:
        response = create_application_in_chirpstack(application)

    set_status(application, response)

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
    if response is None:
        logger.debug(
            f"Application not found. Creating application {application.name} in Chirpstack."
        )
        response = create_application_in_chirpstack(application)

    if response and response.status_code == 200:
        response = requests.put(url, json=payload, headers=HEADERS)

    set_status(application, response)

    return response


def sync_application_destroy(application):
    response = None
    if has_application_id(application) and get_application_by_id(application):
        response = requests.delete(
            f"{CHIRPSTACK_APPLICATION_URL}/{application.cs_application_id}",
            headers=HEADERS,
        )

        if response and response.status_code == 200:
            logger.debug(f"Application deleted in Chirpstack")
            return response

        logger.error(f"Error deleting Application try to delete it manually.")

    return response


def get_applications_from_chirpstack():
    """Sync applications from Chirpstack to local DB per tenant."""
    local_tenants = Tenant.objects.exclude(cs_tenant_id__isnull=True)
    last_response = None

    for tenant in local_tenants:
        workspace = get_or_create_default_workspace(tenant)

        cs_apps, response = fetch_applications(
            tenant, CHIRPSTACK_APPLICATION_URL, HEADERS
        )
        last_response = response

        local_apps = Application.objects.filter(workspace=workspace)
        to_remove = []

        for local_app in local_apps:
            match = next(
                (a for a in cs_apps if a["id"] == local_app.cs_application_id), None
            )
            if match:
                to_remove.append(match)
                update_local_application(local_app, match)

        for match in to_remove:
            cs_apps.remove(match)

        for new_app in cs_apps:
            create_local_application(new_app, workspace)

    return last_response


# Device
def get_device_by_id(device):
    found = False
    if device.dev_eui:
        response = requests.get(
            f"{CHIRPSTACK_DEVICE_URL}/{device.dev_eui}",
            headers=HEADERS,
        )
        if response and response.status_code == 200:
            set_status(device, response)
            found = True
        else:
            logger.debug(f"Device {device.dev_eui} not found in Chirpstack.")
    return found


def create_device_in_chirpstack(device):
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

    found = get_device_by_id(device)
    if not found:
        logger.debug(
            f"Device not found. Creating device {device.dev_eui} in Chirpstack."
        )
        response = requests.post(CHIRPSTACK_DEVICE_URL, json=payload, headers=HEADERS)
        if response and response.status_code == 200:
            logger.debug(f"Device {device.dev_eui} created in Chirpstack.")
            set_status(device, response)
        else:
            logger.error(
                f"Error creating device {device.dev_eui} in Chirpstack: {response.text}"
            )
            set_status(device, response)
        return response
    return None


def sync_device_create(device):
    response = create_device_in_chirpstack(device)
    return response


def sync_device_get(device):
    response = create_device_in_chirpstack(device)
    set_status(device, response)
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

    response = create_device_in_chirpstack(device)

    if response is None or response.status_code == 200:
        logger.debug(f"Updating device {device.dev_eui} in Chirpstack.")
        response = requests.put(url, json=payload, headers=HEADERS)

    set_status(device, response)
    return response


def sync_device_destroy(device):
    response = None
    if device.dev_eui and get_device_by_id(device):
        response = requests.delete(
            f"{CHIRPSTACK_DEVICE_URL}/{device.dev_eui}",
            headers=HEADERS,
        )

        if response and response.status_code == 200:
            logger.debug(f"Device deleted in Chirpstack")
            return response

        logger.error(f"Error deleting Device try to delete it manually.")

    return response


def activate_device(device):
    if not device.activation:
        raise ValueError("Device has no activation data")

    payload = {
        "deviceActivation": {
            "aFCntDown": device.activation.afcntdown,
            "appSKey": device.activation.app_s_key,
            "devAddr": device.activation.dev_addr,
            "fCntUp": device.activation.f_cnt_up,
            "fNwkSIntKey": device.activation.f_nwk_s_int_key,
            "nFCntDown": device.activation.n_f_cnt_down,
            "nwkSEncKey": device.activation.nwk_s_enc_key,
            "sNwkSIntKey": device.activation.s_nwk_s_int_key,
        }
    }
    url = f"{CHIRPSTACK_DEVICE_URL}/{device.dev_eui}/activate"
    response = requests.post(url, json=payload, headers=HEADERS)
    return response


def deactivate_device(device):
    url = f"{CHIRPSTACK_DEVICE_URL}/{device.dev_eui}/activation"
    response = requests.delete(url, headers=HEADERS)
    return response


def device_activation_status(device):
    status = False
    url = f"{CHIRPSTACK_DEVICE_URL}/{device.dev_eui}"
    response = requests.get(url, headers=HEADERS)
    if response and response.status_code == 200:
        activation = response.json().get("device", {}).get("isDisabled", True)

        if not activation:
            last_seen = response.json().get("device", {}).get("lastSeenAt", None)
            if last_seen or last_seen != None:
                status = True

        return status

    else:
        logger.error(
            f"Error fetching device activation status: Device does not exist in Chirpstack or try to check it manually. {response.text} {response.request.url}"
        )

    return status


def get_devices_from_chirpstack():
    """Sync devices from Chirpstack to local DB per application."""
    local_apps = Application.objects.exclude(cs_application_id__isnull=True)
    last_response = None

    for app in local_apps:
        workspace = app.workspace
        cs_devices, response = fetch_devices(app, CHIRPSTACK_DEVICE_URL, HEADERS)
        last_response = response

        local_devices = Device.objects.filter(application=app)
        to_remove = []

        for local_dev in local_devices:
            match = next(
                (d for d in cs_devices if d["devEui"] == local_dev.dev_eui), None
            )
            if match:
                to_remove.append(match)
                update_local_device(local_dev, match)

        for match in to_remove:
            cs_devices.remove(match)

        for new_dev in cs_devices:
            create_local_device(new_dev, app, workspace)

    return last_response
