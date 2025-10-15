import datetime as dt
from loguru import logger
import requests
from .models import ApiUser, DeviceProfile
from organizations.helpers import get_or_create_default_workspace, get_emasa_tenant
from infrastructure.models import Application, Type, Machine, Device


def fetch_chirpstack_users(api_url, headers):
    """Fetch global users from Chirpstack API."""
    response = requests.get(api_url, headers=headers, params={"limit": 100})
    if response.status_code == 200:
        return response.json().get("result", []), response
    return [], response


def fetch_tenant_user_mapping(tenants, tenant_url, headers):
    """Map Chirpstack user IDs to their tenants and roles."""
    mapping = {}
    for tenant in tenants:
        if not tenant.cs_tenant_id:
            continue
        resp = requests.get(
            f"{tenant_url}/{tenant.cs_tenant_id}/users",
            headers=headers,
            params={"limit": 100},
        )
        if resp.status_code != 200:
            continue

        tenant_users = resp.json().get("result", [])
        for tu in tenant_users:
            uid = tu["userId"]
            mapping.setdefault(uid, []).append(
                {
                    "tenant": tenant,
                    "isAdmin": tu.get("isAdmin", False),
                    "isDeviceAdmin": tu.get("isDeviceAdmin", False),
                    "isGatewayAdmin": tu.get("isGatewayAdmin", False),
                }
            )
    return mapping


def resolve_workspace_for_user(user_id, user_tenant_mapping):
    """Ensure user always has a workspace. Falls back to 'emasa tenant' if none."""
    tenant_info_list = user_tenant_mapping.get(user_id, [])
    if tenant_info_list:
        tenant = tenant_info_list[0]["tenant"]
    else:
        tenant = get_emasa_tenant()
    return get_or_create_default_workspace(tenant), tenant_info_list


def update_existing_user(instance, match, user_tenant_mapping):
    """Update fields for an existing ApiUser instance from Chirpstack data."""
    instance.cs_user_id = match["id"]
    instance.is_active = match.get("isActive", instance.is_active)
    instance.is_admin = match.get("isAdmin", instance.is_admin)
    instance.note = match.get("note", instance.note)
    instance.sync_status = "SYNCED"
    instance.sync_error = ""
    instance.last_synced_at = dt.datetime.now()

    workspace, tenant_info_list = resolve_workspace_for_user(
        match["id"], user_tenant_mapping
    )
    instance.workspace = workspace
    if tenant_info_list:
        instance.is_tenant_admin = tenant_info_list[0]["isAdmin"]

    instance.save()


def create_new_user(new_instance, user_tenant_mapping):
    """Create a new ApiUser in local DB from Chirpstack data."""
    if ApiUser.objects.filter(email=new_instance["email"]).exists():
        return None

    workspace, tenant_info_list = resolve_workspace_for_user(
        new_instance["id"], user_tenant_mapping
    )

    api_user = ApiUser(
        email=new_instance["email"],
        cs_user_id=new_instance["id"],
        is_active=new_instance["isActive"],
        is_admin=new_instance["isAdmin"],
        note=new_instance.get("note", ""),
        workspace=workspace,
        password="",
        sync_error="Please set a new password and assign this user to a desired workspace",
        sync_status="SYNCED",
        last_synced_at=dt.datetime.now(),
    )

    if tenant_info_list:
        api_user.is_tenant_admin = tenant_info_list[0]["isAdmin"]
        api_user.is_tenant_device_admin = tenant_info_list[0]["isDeviceAdmin"]
        api_user.is_tenant_gateway_admin = tenant_info_list[0]["isGatewayAdmin"]

    api_user.save()
    return api_user


def fetch_device_profiles(tenant, device_profile_url, headers):
    """Fetch device profiles for a tenant from Chirpstack."""
    response = requests.get(
        device_profile_url,
        headers=headers,
        params={"limit": 100, "tenantId": tenant.cs_tenant_id},
    )
    if response.status_code != 200:
        logger.error(f"Error fetching device profiles for tenant {tenant.cs_tenant_id}")
        return [], response
    return response.json().get("result", []), response


def update_local_device_profile(local_dp, match, workspace):
    """Update fields for a local DeviceProfile based on Chirpstack data."""
    local_dp.name = match.get("name", local_dp.name)
    local_dp.description = match.get("description", local_dp.description)
    local_dp.region = match.get("region", local_dp.region)
    local_dp.adr_algorithm_id = match.get("adrAlgorithmId", local_dp.adr_algorithm_id)
    local_dp.mac_version = match.get("macVersion", local_dp.mac_version)
    local_dp.reg_param_revision = match.get(
        "regParamsRevision", local_dp.reg_param_revision
    )
    local_dp.supports_otaa = match.get("supportsOtaa", local_dp.supports_otaa)
    local_dp.supports_class_b = match.get("supportsClassB", local_dp.supports_class_b)
    local_dp.supports_class_c = match.get("supportsClassC", local_dp.supports_class_c)
    local_dp.abp_rx1_delay = match.get("abpRx1Delay", local_dp.abp_rx1_delay)
    local_dp.abp_rx1_dr_offset = match.get("abpRx1DrOffset", local_dp.abp_rx1_dr_offset)
    local_dp.abp_rx2_dr = match.get("abpRx2Dr", local_dp.abp_rx2_dr)
    local_dp.abp_rx2_freq = match.get("abpRx2Freq", local_dp.abp_rx2_freq)
    local_dp.is_rlay = match.get("isRelay", local_dp.is_rlay)
    local_dp.is_rlay_ed = match.get("isRelayEd", local_dp.is_rlay_ed)
    local_dp.flush_queue_on_activate = match.get(
        "flushQueueOnActivate", local_dp.flush_queue_on_activate
    )
    local_dp.uplink_interval = match.get("uplinkInterval", local_dp.uplink_interval)
    local_dp.workspace = workspace
    local_dp.sync_status = "SYNCED"
    local_dp.sync_error = ""
    local_dp.last_synced_at = dt.datetime.now()
    local_dp.save()
    logger.debug(
        f"DeviceProfile {local_dp.cs_device_profile_id} - {local_dp.name} updated"
    )


def create_local_device_profile(new_dp, workspace):
    """Create a new DeviceProfile in local DB from Chirpstack data."""
    dp = DeviceProfile(
        cs_device_profile_id=new_dp["id"],
        name=new_dp["name"],
        description="Imported from Chirpstack",
        region=new_dp.get("region", ""),
        workspace=workspace,
        mac_version=new_dp.get("macVersion", "LORAWAN_1_0_3"),
        reg_param_revision=new_dp.get("regParamsRevision", "A"),
        adr_algorithm_id=new_dp.get("adrAlgorithmId", "default"),
        payload_codec_runtime=new_dp.get("payloadCodecRuntime", ""),
        payload_codec_script=new_dp.get("payloadCodecScript", ""),
        is_rlay=new_dp.get("isRelay", False),
        is_rlay_ed=new_dp.get("isRelayEd", False),
        abp_rx1_delay=new_dp.get("abpRx1Delay", 1),
        abp_rx1_dr_offset=new_dp.get("abpRx1DrOffset", 0),
        abp_rx2_dr=new_dp.get("abpRx2Dr", 0),
        abp_rx2_freq=new_dp.get("abpRx2Freq", 0),
        supports_otaa=new_dp.get("supportsOtaa", False),
        supports_class_b=new_dp.get("supportsClassB", False),
        supports_class_c=new_dp.get("supportsClassC", False),
        sync_status="SYNCED",
        sync_error="",
        last_synced_at=dt.datetime.now(),
    )
    dp.save()
    logger.debug(
        f"DeviceProfile {dp.cs_device_profile_id} - {dp.name} created from Chirpstack"
    )
    return dp


def fetch_applications(tenant, application_url, headers):
    """Fetch applications for a tenant from Chirpstack."""
    response = requests.get(
        application_url,
        headers=headers,
        params={"limit": 100, "tenantId": tenant.cs_tenant_id},
    )
    if response.status_code != 200:
        logger.error(f"Error fetching applications for tenant {tenant.cs_tenant_id}")
        return [], response
    return response.json().get("result", []), response


def update_local_application(local_app, match):
    """Update an existing local Application with Chirpstack data."""
    local_app.name = match.get("name", local_app.name)
    local_app.description = match.get("description", local_app.description)
    local_app.sync_status = "SYNCED"
    local_app.sync_error = ""
    local_app.last_synced_at = dt.datetime.now()
    local_app.save()
    logger.debug(
        f"Application {local_app.cs_application_id} - {local_app.name} updated"
    )


def create_local_application(new_app, workspace):
    """Create a new Application in the local DB from Chirpstack data."""
    default_type = Type.objects.filter(name="Generic").first()
    if not default_type:
        default_type = Type.objects.create(
            name="Generic", description="Generic device type"
        )

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
    logger.debug(
        f"Application {app.cs_application_id} - {app.name} created from Chirpstack"
    )
    return app


def fetch_devices(app, device_url, headers):
    """Fetch devices for a given application from Chirpstack."""
    response = requests.get(
        device_url,
        headers=headers,
        params={"limit": 100, "applicationId": app.cs_application_id},
    )
    if response.status_code != 200:
        logger.error(f"Error fetching devices for application {app.cs_application_id}")
        return [], response
    return response.json().get("result", []), response


def get_device_profile(profile_id):
    """Return DeviceProfile by Chirpstack ID or None if not found."""
    try:
        return DeviceProfile.objects.get(cs_device_profile_id=profile_id)
    except DeviceProfile.DoesNotExist:
        logger.warning(f"DeviceProfile {profile_id} not found")
        return None


def update_local_device(local_dev, match):
    """Update an existing local Device with Chirpstack data."""
    dp = DeviceProfile.objects.filter(
        cs_device_profile_id=match["deviceProfileId"]
    ).first()

    local_dev.name = match.get("name", local_dev.name)
    local_dev.description = match.get("description", local_dev.description)
    local_dev.device_profile = dp if dp else local_dev.device_profile
    local_dev.last_seen_at = match.get("lastSeenAt")
    local_dev.sync_status = "SYNCED"
    local_dev.sync_error = ""
    local_dev.last_synced_at = dt.datetime.now()
    local_dev.save()
    logger.debug(f"Device {local_dev.dev_eui} updated")


def create_local_device(new_dev, app, workspace):
    """Create a new Device in the local DB from Chirpstack data."""
    dp = DeviceProfile.objects.filter(
        cs_device_profile_id=new_dev["deviceProfileId"]
    ).first()

    default_type = Type.objects.filter(name="Generic").first()
    if not default_type:
        default_type = Type.objects.create(
            name="Generic", description="Generic device type"
        )

    default_machine = Machine.objects.filter(name="Generic Machine").first()
    if not default_machine:
        default_machine = Machine.objects.create(
            name="Generic Machine",
            workspace=workspace,
            description="Default machine",
        )

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
    logger.debug(f"Device {dev.dev_eui} - {dev.name} created from Chirpstack")
    return dev
