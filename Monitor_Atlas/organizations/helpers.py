from .models import Workspace, Subscription, Tenant
from roles.models import Role, WorkspaceMembership
from roles.helpers import (
    assign_base_tenant_admin_permissions_to_group,
    assign_base_workspace_admin_permissions_to_group,
)


def get_or_create_default_workspace(tenant):
    """
    Retrieves the default workspace for the given tenant.
    If it doesn't exist, creates one.
    Also ensures that a "No Role" role exists within that workspace.
    """
    workspace = Workspace.objects.filter(tenant=tenant, name="Default").first()
    if not workspace:
        workspace = Workspace.objects.create(
            tenant=tenant,
            name="Default",
            description="Default workspace",
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


def get_emasa_tenant():
    tenant = Tenant.objects.get(name="EMASA")
    return tenant


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
    if created:
        assign_base_tenant_admin_permissions_to_group(workspace.tenant, role.group)
        assign_base_workspace_admin_permissions_to_group(workspace, role.group)

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
