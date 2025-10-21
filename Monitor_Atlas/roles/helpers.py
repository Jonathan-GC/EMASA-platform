# Guardian helpers
from guardian.shortcuts import assign_perm, remove_perm, get_perms, get_objects_for_user
from loguru import logger

from .models import WorkspaceMembership
from infrastructure.models import Device, Machine, Gateway, Application
from organizations.models import Workspace


def assign_workspace_permissions(user, workspace, role):
    """Assign permissions for a user in a specific workspace based on their role.

    Keyword arguments:
    user -- the user to assign permissions to
    workspace -- the workspace to assign permissions in
    role -- the role of the user in the workspace
    Return: None
    """

    logger.debug(
        f"Assigning workspace permissions: user={user}, workspace={workspace}, role={role}"
    )
    # Base perms for all users
    assign_perm("organizations.view_workspace", user, workspace)

    if role.is_admin:
        assign_perm("organizations.change_workspace", user, workspace)
        assign_perm("organizations.manage_workspace", user, workspace)
        assign_perm("roles.manage_roles", user)
        assign_perm("roles.manage_memberships", user)
        logger.debug(f"Assigned admin permissions to {user}")


def assign_object_permissions(user, obj, permissions=None):
    """Assign object-level permissions to a user for a specific object.

    Keyword arguments:
    user -- the user to assign permissions to
    obj -- the object to assign permissions for
    permissions -- a list of permissions to assign (default: None)
    Return: None
    """

    app_label = obj._meta.app_label
    model_name = obj._meta.model_name

    if permissions is None:

        if hasattr(obj, "workspace"):
            # Workspace-level permissions
            membership = WorkspaceMembership.objects.filter(
                user=user, workspace=obj.workspace
            ).first()
            if membership and membership.role.is_admin:
                permissions = ["view", "change", "delete", "manage"]
            else:
                permissions = ["view"]
        else:
            # Default to view permission
            permissions = ["view"]

    for perm in permissions:
        perm_codename = f"{perm}_{model_name}"
        full_perm = f"{app_label}.{perm_codename}"
        try:
            assign_perm(full_perm, user, obj)
            logger.debug(f"Assigned permission {full_perm} to {user} for {obj}")
        except Exception as e:
            logger.error(
                f"Failed to assign permission {full_perm} to {user} for {obj}: {e}"
            )


def assign_role_permissions(user, role, workspace):
    """Assign permissions for a user in a specific workspace based on their role.

    Keyword arguments:
    user -- the user to assign permissions to
    role -- the role of the user in the workspace
    workspace -- the workspace to assign permissions in
    Return: None
    """

    logger.debug(
        f"Assigning role permissions: user={user}, role={role}, workspace={workspace}"
    )
    # Assign base workspace permission
    assign_perm("organizations.view_workspace", user, workspace)

    if role.is_admin:
        models = [Device, Machine, Gateway, Application]

        for model_class in models:

            model_name = model_class._meta.model_name
            objects = model_class.objects.filter(workspace=workspace)

            for obj in objects:
                # Non super-tenant or superuser read only
                assign_perm(f"infrastructure.view_{model_name}", user, obj)

            logger.debug(
                f"Assigned admin permissions for {model_name} to {user} in {workspace} **Infrastructure view only**"
            )
    else:
        logger.debug(f"Non admin users must be assigned permissions individually")


def remove_workspace_permissions(user, workspace):
    """Remove all permissions for a user in a specific workspace.

    Keyword arguments:
    user -- the user to remove permissions from
    workspace -- the workspace to remove permissions in
    Return: None
    """

    logger.debug(f"Removing workspace permissions: user={user}, workspace={workspace}")

    # Remove all permissions for the user in the workspace
    remove_perm("organizations.view_workspace", user, workspace)
    remove_perm("organizations.change_workspace", user, workspace)
    remove_perm("organizations.manage_workspace", user, workspace)

    models = [Device, Machine, Gateway, Application]

    for model_class in models:
        model_name = model_class._meta.model_name
        objects = model_class.objects.filter(workspace=workspace)

        for obj in objects:
            remove_perm(f"view_{model_name}", user, obj)
            remove_perm(f"change_{model_name}", user, obj)
            remove_perm(f"delete_{model_name}", user, obj)
            remove_perm(f"manage_{model_name}", user, obj)

    logger.debug(f"Removed all permissions for {user} in {workspace}")


def get_user_permissions_summary(user, workspace=None):
    """
    Get a summary of user permissions.

    Args:
        user: User
        workspace: Optional workspace to filter by

    Returns:
        dict: Summary of permissions
    """
    summary = {"user": str(user), "is_superuser": user.is_superuser, "workspaces": []}

    if workspace:
        workspaces = [workspace]
    else:
        workspaces = get_objects_for_user(
            user, "organizations.view_workspace", klass=Workspace
        )

    for ws in workspaces:
        ws_data = {
            "workspace": str(ws),
            "permissions": get_perms(user, ws),
            "devices": Device.objects.filter(workspace=ws).count(),
            "machines": Machine.objects.filter(workspace=ws).count(),
            "gateways": Gateway.objects.filter(workspace=ws).count(),
            "applications": Application.objects.filter(workspace=ws).count(),
        }
        summary["workspaces"].append(ws_data)

    return summary
