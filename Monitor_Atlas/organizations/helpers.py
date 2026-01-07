from .models import Workspace, Subscription, Tenant
from roles.models import Role, WorkspaceMembership
from roles.helpers import (
    assign_base_tenant_admin_permissions_to_group,
    assign_base_workspace_admin_permissions_to_group,
)
from django.contrib.auth.models import Group
from loguru import logger
from guardian.shortcuts import assign_perm, remove_perm, get_perms


GLOBAL_ADMIN_ROLE_GROUP_NAME = "global_admin"
GLOBAL_ADMIN_ROLE_GROUP = None


def get_global_admin_role_group():
    """Return the global admin Group, or None if it cannot be loaded.

    This avoids querying the database at import time (which can fail during
    migrations/startup). Callers should handle a None return value.
    """
    try:
        return Group.objects.get(name=GLOBAL_ADMIN_ROLE_GROUP_NAME)
    except Exception:
        return None


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
        global_group = get_global_admin_role_group()
        if global_group:
            assign_perm("view_workspace", global_group, workspace)
            assign_perm("change_workspace", global_group, workspace)
            assign_perm("delete_workspace", global_group, workspace)

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


def get_global_tenant():
    tenant = Tenant.objects.get(is_global=True)
    return tenant


def get_no_role(workspace):
    """
    Retrieves the "No Role" role for the given workspace.
    If it doesn't exist, creates one.
    """
    role, created = Role.objects.get_or_create(
        workspace=workspace,
        name="Sin rol",
        defaults={"description": "Usuario sin rol ni permisos", "color": "#cccccc"},
    )

    if created or not role.group:
        if not role.group:
            group, _ = Group.objects.get_or_create(
                name=f"{role.id}_{role.name}_{workspace.tenant.name}"
            )
            if _:
                logger.debug(f"Created group {group.name} for No Role")
            role.group = group
            role.save()
        global_group = get_global_admin_role_group()
        if global_group:
            assign_perm("view_role", global_group, role)
            assign_perm("change_role", global_group, role)
            assign_perm("delete_role", global_group, role)

    return role


def get_or_create_admin_role(workspace):
    """
    Retrieves the admin role for the given workspace.
    If it doesn't exist, creates one.
    """
    role, created = Role.objects.get_or_create(
        workspace=workspace,
        name="Admin",
        defaults={"is_admin": True, "color": "#ebcc34"},
    )
    if created or not role.group:
        if not role.group:
            group, _ = Group.objects.get_or_create(
                name=f"{role.id}_{role.name}_{workspace.tenant.name}"
            )
            if _:
                logger.debug(f"Created group {group.name} for admin role")
            role.group = group
            role.save()

        assign_base_tenant_admin_permissions_to_group(workspace.tenant, role.group)
        assign_base_workspace_admin_permissions_to_group(workspace, role.group)
        global_group = get_global_admin_role_group()
        if global_group:
            assign_perm("view_role", global_group, role)
            assign_perm("change_role", global_group, role)
            assign_perm("delete_role", global_group, role)

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
