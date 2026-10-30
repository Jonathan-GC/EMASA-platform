from django.contrib.auth.models import Group

from infrastructure.models import Device
from users.models import User
from roles.models import WorkspaceMembership
from roles.permissions import has_contextual_perm


def get_users_for_device(dev_eui):
    """Return all users who can view ``dev_eui`` according to the contextual
    permission engine.

    The contextual engine (``roles.permissions.has_contextual_perm``) grants
    ``view_device`` via shortcuts that are NOT persisted as Guardian object
    permissions on the device (workspace admins by name, tenant owners,
    superusers, global admins, hall-pass holders). Resolving recipients purely
    from Guardian rows therefore misses most real recipients, so we enumerate
    the candidate users affiliated with the device's tenant/workspace and filter
    them through the same engine that enforces access.
    """
    device = (
        Device.objects.select_related("workspace", "workspace__tenant")
        .filter(dev_eui__iexact=dev_eui)
        .first()
    )
    if not device:
        raise ValueError(f"Device with dev_eui '{dev_eui}' not found.")

    workspace = device.workspace
    tenant = workspace.tenant if workspace else None

    # Candidate users: anyone affiliated with the device's tenant/workspace,
    # plus global role groups and superusers.
    affiliated_ids = set(
        WorkspaceMembership.objects.filter(workspace__tenant=tenant).values_list(
            "user_id", flat=True
        )
    )
    affiliated_ids |= set(
        User.objects.filter(tenant=tenant).values_list("id", flat=True)
    )
    global_groups = Group.objects.filter(
        name__in=["global_admin", "global_manager", "global_technician"]
    )
    affiliated_ids |= set(
        User.objects.filter(groups__in=global_groups).values_list("id", flat=True)
    )
    affiliated_ids |= set(
        User.objects.filter(is_superuser=True).values_list("id", flat=True)
    )

    result = []
    seen = set()
    for user in User.objects.filter(id__in=affiliated_ids):
        try:
            if has_contextual_perm(
                user, "view_device", tenant=tenant, workspace=workspace, obj=device
            ):
                if user.id not in seen:
                    seen.add(user.id)
                    result.append(user)
        except Exception:
            continue

    if not result:
        raise ValueError(
            f"No users found with permission to view device '{dev_eui}'."
        )
    return result
