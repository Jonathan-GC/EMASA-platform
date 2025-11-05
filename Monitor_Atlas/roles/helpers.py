from guardian.shortcuts import assign_perm, remove_perm
from loguru import logger


def assign_new_user_base_permissions(user):
    """
    Assign base permissions to a new user.
    Permissions includes:
    - Creating a tenant
    - Permission to modify/delete itself

    Args:
        user (User): The user object to assign permissions to.
    """
    assign_perm("users.view_user", user, user)
    assign_perm("users.change_user", user, user)
    assign_perm("users.delete_user", user, user)

    if user.tenant is not None:
        assign_perm("organizations.view_tenant", user, user.tenant)
        logger.debug(f"Assigned tenant member view permission to user {user.username}")
        return

    assign_perm("organizations.add_tenant", user)
    logger.debug(f"Assigned base permissions to user {user.username}")

    user.save()


def assign_new_tenant_base_permissions(tenant, user):
    """
    Assign base permissions to a new tenant owner.
    Permissions includes:
    - Permission to modify/view itself
    - Deletion must be requested through support

    Args:
        tenant (Tenant): The tenant object to assign permissions to.
        user (User): The user object to assign permissions to.
    """

    assign_perm("organizations.view_tenant", user, tenant)
    assign_perm("organizations.change_tenant", user, tenant)

    # Workspace creation permission is given to tenant owners
    assign_perm("organizations.add_workspace", user)

    # Tenant creation is just one time usage
    remove_perm("organizations.add_tenant", user)

    user.save()


def assign_new_workspace_base_permissions(workspace, user):
    """
    Assign base permissions to a new workspace owner.
    Permissions includes:
    - Permission to modify/view itself
    - Permission to delete itself
    - Deleting must be requested through support

    Args:
        workspace (Workspace): The workspace object to assign permissions to.
        user (User): The user object to assign permissions to.
    """

    assign_perm("workspaces.view_workspace", user, workspace)
    assign_perm("workspaces.change_workspace", user, workspace)

    # Role creation permission is given to workspace owners
    assign_perm("roles.add_role", user)

    # Machine creation permission is given to workspace owners
    assign_perm("infrastructure.add_machine", user)

    user.save()


def assign_new_role_base_permissions(role, user):
    """
    Assign base permissions to a new role owner.
    Permissions includes:
    - Permission to modify/view itself
    - Permission to delete itself

    Args:
        role (Role): The role object to assign permissions to.
        user (User): The user object to assign permissions to.
    """

    assign_perm("roles.view_role", user, role)
    assign_perm("roles.change_role", user, role)
    assign_perm("roles.delete_role", user, role)

    user.save()


def assign_created_instance_permissions(instance, user):
    """
    Assign base permissions to a newly created instance.
    Permissions includes:
    - Permission to modify/view itself
    - Permission to delete itself

    Args:
        instance (Model): The instance object to assign permissions to.
        user (User): The user object to assign permissions to.
    """

    model_name = instance._meta.model_name

    view_perm = f"{model_name}.view_{model_name}"
    change_perm = f"{model_name}.change_{model_name}"
    delete_perm = f"{model_name}.delete_{model_name}"

    assign_perm(view_perm, user, instance)
    assign_perm(change_perm, user, instance)
    assign_perm(delete_perm, user, instance)

    user.save()


def support_manager_can_view_all_support_members(support_manager, user):
    """
    Assign support member permissions to a support manager for a specific user.
    Permissions includes:
    - Permission to view user
    """

    assign_perm("users.view_user", support_manager, user)

    user.save()


def assign_base_tenant_admin_permissions_to_group(tenant, group):
    """
    Assign base tenant admin permissions to a group.
    Permissions includes:
    - Permission to modify/view/delete tenant
    - Permission to add workspaces
    """

    assign_perm("organizations.view_tenant", group, tenant)
    assign_perm("organizations.change_tenant", group, tenant)

    # Workspace creation permission is given to tenant admins
    assign_perm("organizations.add_workspace", group)

    logger.debug(f"Assigned base tenant admin permissions to group {group.name}")

    group.save()


def assign_base_workspace_admin_permissions_to_group(workspace, group):
    """
    Assign base workspace admin permissions to a group.
    Permissions includes:
    - Permission to modify/view/delete workspace
    - Permission to add roles
    - Permission to add machines
    """

    assign_perm("workspaces.view_workspace", group, workspace)
    assign_perm("workspaces.change_workspace", group, workspace)

    # Role creation permission is given to workspace admins
    assign_perm("roles.add_role", group)
    # Machine creation permission is given to workspace admins
    assign_perm("infrastructure.add_machine", group)

    logger.debug(f"Assigned base workspace admin permissions to group {group.name}")

    group.save()
