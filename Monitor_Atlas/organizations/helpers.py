from .models import Workspace, Subscription
from roles.models import Role, WorkspaceMembership, RolePermission, PermissionKey


def get_or_create_default_workspace(tenant):
    """
    Retrieves the default workspace for the given tenant.
    If it doesn't exist, creates one.
    Also ensures that a "No Role" role exists within that workspace.
    """
    workspace, created = Workspace.objects.get_or_create(
        tenant=tenant, defaults={"name": f"{tenant.name} Workspace"}
    )

    no_role = Role.objects.get_or_create(
        workspace=workspace,
        name="Sin Rol",
        defaults={"description": "Usuario sin rol ni permisos", "color": "#cccccc"},
    )

    return workspace


def get_or_create_default_subscription():
    """
    Retrieves the default subscription.
    If it doesn't exist, creates one.
    """

    subscription, created = Subscription.objects.get_or_create(
        name="Trial Plan",
        defaults={
            "description": "Default trial plan with limited features",
            "can_have_gateways": True,
            "max_device_count": 5,
            "max_gateway_count": 1,
        },
    )
    return subscription


def get_no_role(workspace):
    """
    Retrieves the "No Role" role for the given workspace.
    If it doesn't exist, creates one.
    """
    role, created = Role.objects.get_or_create(
        workspace=workspace,
        name="Sin Rol",
        defaults={"description": "Usuario sin rol ni permisos", "color": "#cccccc"},
    )
    return role


def get_or_create_admin_role(workspace):
    """
    Retrieves the admin role for the given workspace.
    If it doesn't exist, creates one.
    """
    role, created = Role.objects.get_or_create(
        workspace=workspace,
        defaults={"name": "Admin", "is_admin": True, "color": "#ebcc34"},
    )
    return role


def add_user_to_workspace(user, workspace):
    """
    Adds a user to a workspace with the specified role.
    If no role is provided, assigns the default admin role.
    """

    role = get_no_role(workspace)

    membership, created = WorkspaceMembership.objects.get_or_create(
        workspace=workspace, user=user, role=role
    )

    if not created:
        membership.role = role
        membership.save()

    return membership


def add_permission_to_role(role, permission_key):
    """
    Adds a permission key to a role if it doesn't already exist.
    """

    role_permission, created = RolePermission.objects.get_or_create(
        role=role, permission_key=permission_key
    )
    return role_permission
