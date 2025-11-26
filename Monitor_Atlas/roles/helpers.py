from guardian.shortcuts import assign_perm, remove_perm, get_perms
from loguru import logger
from organizations.models import Tenant, Workspace
from users.models import User
from roles.models import Role
from .global_helpers import GLOBAL_PERMISSIONS_PRESET, get_monitor_tenant
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Group

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


def get_user_group(user):
    try:
        user = User.objects.get(id=user.id)
        if user.is_superuser:
            return get_global_admin_role_group()

        role = Role.objects.filter(
            workspacemembership__user=user,
            workspacemembership__workspace__tenant=user.tenant,
        ).first()
        if role and role.group:
            return role.group
    except Exception:
        pass


def assign_new_user_base_permissions(user):
    """
    Assign base permissions to a new user.
    Permissions includes:
    - Creating a tenant
    - Permission to modify/delete itself

    Args:
        user (User): The user object to assign permissions to.
    """
    assign_perm("view_user", user, user)
    assign_perm("change_user", user, user)
    assign_perm("delete_user", user, user)

    if user.tenant is not None:
        tenant = Tenant.objects.get(id=user.tenant.id)
        assign_perm("view_tenant", user, tenant)
        logger.debug(f"Assigned tenant member view permission to user {user.username}")
        user.save()
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

    assign_perm("view_tenant", user, tenant)
    assign_perm("change_tenant", user, tenant)
    assign_perm("users.add_user", user)

    # Workspace creation permission is given to tenant owners
    assign_perm("organizations.add_workspace", user)

    # Tenant creation is just one time usage
    remove_perm("organizations.add_tenant", user)

    global_group = get_global_admin_role_group()
    if global_group:
        assign_perm("view_tenant", global_group, tenant)
        assign_perm("change_tenant", global_group, tenant)
        assign_perm("delete_tenant", global_group, tenant)

    user.save()


def assign_new_workspace_base_permissions(workspace, user):
    """
    Assign base permissions to a new workspace owner.
    Permissions includes:
    - Permission to modify/view/delete itself
    - Deleting must be requested through support

    Args:
        workspace (Workspace): The workspace object to assign permissions to.
        user (User): The user object to assign permissions to.
    """

    assign_perm("view_workspace", user, workspace)
    assign_perm("change_workspace", user, workspace)
    assign_perm("delete_workspace", user, workspace)

    assign_perm("roles.add_role", user)
    assign_perm("infrastructure.add_machine", user)

    global_group = get_global_admin_role_group()
    if global_group:
        assign_perm("view_workspace", global_group, workspace)
        assign_perm("change_workspace", global_group, workspace)
        assign_perm("delete_workspace", global_group, workspace)

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

    assign_perm("view_role", user, role)
    assign_perm("change_role", user, role)
    assign_perm("delete_role", user, role)

    global_group = get_global_admin_role_group()
    if global_group:
        assign_perm("view_role", global_group, role)
        assign_perm("change_role", global_group, role)
        assign_perm("delete_role", global_group, role)

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
    app_label = instance._meta.app_label
    instance_workspace = getattr(instance, "workspace", None)

    view_perm = f"view_{model_name}"
    change_perm = f"change_{model_name}"
    delete_perm = f"delete_{model_name}"

    user_group = get_user_group(user)
    if user_group:
        assign_perm(view_perm, user_group, instance)
        assign_perm(change_perm, user_group, instance)
        assign_perm(delete_perm, user_group, instance)
    else:
        logger.debug(
            f"The user: {user.username} has no group assigned, skipping group permissions."
        )

    global_group = get_global_admin_role_group()
    if global_group:
        assign_perm(view_perm, global_group, instance)
        assign_perm(change_perm, global_group, instance)
        assign_perm(delete_perm, global_group, instance)

    if instance_workspace:
        admin_role = Role.objects.filter(
            workspace=instance_workspace, is_admin=True
        ).first()
        if admin_role and admin_role.group:
            assign_perm(view_perm, admin_role.group, instance)
            assign_perm(change_perm, admin_role.group, instance)
            assign_perm(delete_perm, admin_role.group, instance)

    if app_label in ["organizations", "roles", "users"]:
        manager_group = Group.objects.filter(name="global_manager").first()
        if manager_group:
            assign_perm(view_perm, manager_group, instance)
            assign_perm(change_perm, manager_group, instance)
            assign_perm(delete_perm, manager_group, instance)
    elif app_label in ["infrastructure", "chirpstack"]:
        support_group = Group.objects.filter(name="global_technician").first()
        if support_group:
            assign_perm(view_perm, support_group, instance)
            assign_perm(change_perm, support_group, instance)
            assign_perm(delete_perm, support_group, instance)

    user.save()


def support_manager_can_view_all_support_members(support_manager, user):
    """
    Assign support member permissions to a support manager for a specific user.
    Permissions includes:
    - Permission to view user
    """

    user = User.objects.get(id=user.id)
    support_manager = User.objects.get(id=support_manager.id)

    assign_perm("view_user", support_manager, user)

    user.save()


def assign_base_tenant_admin_permissions_to_group(tenant, group):
    """
    Assign base tenant admin permissions to a group.
    Permissions includes:
    - Permission to modify/view/delete tenant
    - Permission to add workspaces
    """

    assign_perm("view_tenant", group, tenant)
    assign_perm("change_tenant", group, tenant)

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

    app_label = workspace._meta.app_label
    assign_perm(f"view_workspace", group, workspace)
    assign_perm(f"change_workspace", group, workspace)

    # Role creation permission is given to workspace admins
    assign_perm("roles.add_role", group)
    assign_perm("roles.add_workspacemembership", group)
    # Machine creation permission is given to workspace admins
    assign_perm("infrastructure.add_machine", group)

    logger.debug(f"Assigned base workspace admin permissions to group {group.name}")

    group.save()


def get_user_workspace_admin_status(user, workspace):
    """
    Check if a user has admin permissions for a specific workspace.

    Args:
        user (User): The user object to check permissions for.
        workspace (Workspace): The workspace object to check against.
    Returns:
        bool: True if the user has admin permissions for the workspace, False otherwise.
    """

    change_perm = "change_workspace"

    if change_perm in get_perms(user, workspace):
        return True
    logger.debug(
        f"User permissions {get_perms(user, workspace)} do not include admin rights for workspace {workspace.name}"
    )

    return False


def get_assignable_permissions(user, workspace, role):
    """
    Returns all permissions a role may assign inside a workspace.
    """

    assignable_permissions = {"global": {}, "object": {}}

    # --- Check workspace-level admin ---
    is_admin = get_user_workspace_admin_status(user, workspace)
    if not is_admin and user.is_superuser:
        is_admin = True

    if not is_admin or role.name == "Sin rol":
        return assignable_permissions

    group = role.group

    if user and user.is_superuser:
        group = get_global_admin_role_group() or group

    is_global_tenant = workspace.tenant == get_monitor_tenant()

    # --- Object models related to workspace ---
    object_models = {
        "tenant": (
            "organizations",
            [workspace.tenant] if workspace.tenant else [],
        ),
        "workspace": ("organizations", [workspace]),
        "device": ("infrastructure", workspace.device_set.all()),
        "gateway": ("infrastructure", workspace.gateway_set.all()),
        "application": ("infrastructure", workspace.application_set.all()),
        "machine": ("infrastructure", workspace.machine_set.all()),
        "deviceprofile": ("chirpstack", workspace.deviceprofile_set.all()),
        "apiuser": ("chirpstack", workspace.apiuser_set.all()),
        "role": ("roles", workspace.role_set.all()),
        "workspacemembership": ("roles", workspace.workspacemembership_set.all()),
    }

    # --- Permissions allowed per tenant type ---
    full_actions = ["view", "change", "delete"]
    safe_actions = ["view", "change"]
    allowed_actions = full_actions if is_global_tenant else safe_actions

    # --- Object-level permissions ---
    for model_name, (app_label, queryset) in object_models.items():
        assignable_permissions["object"][model_name] = []

        ct = ContentType.objects.get(app_label=app_label, model=model_name)

        for obj in queryset:
            perms_for_obj = {}

            for action in allowed_actions:
                codename = f"{action}_{model_name}"

                # Check object-level permission
                has = codename in get_perms(group, obj)

                # Check global permission fallback
                if not has:
                    if group.permissions.filter(
                        content_type=ct, codename=codename
                    ).exists():
                        has = True

                perms_for_obj[codename] = has

            assignable_permissions["object"][model_name].append(
                {
                    "id": obj.id,
                    "name": str(obj),
                    "permissions": perms_for_obj,
                }
            )
    return assignable_permissions


def bulk_assign_permissions(permissions, role):
    group = role.group
    if role.name == "Sin rol":
        logger.warning(
            f"Attempted to bulk assign permissions to 'Sin rol' role. Operation aborted. Change user's role first."
        )
        return
    logger.info(f"Bulk permission assign for group={group.name}")
    valid_keys = {"assign", "revoke"}
    permissions = {k: v for k, v in permissions.items() if k in valid_keys}

    # Build model->app mapping
    MODEL_MAPPING = {}
    for preset_name, apps in GLOBAL_PERMISSIONS_PRESET.items():
        for app_label, models in apps.items():
            for model_name in models:
                MODEL_MAPPING[model_name] = app_label

    # -------------------------------
    # ASSIGN
    # -------------------------------
    if "assign" in permissions:
        for model_name, perms_dict in permissions["assign"].items():
            if model_name not in MODEL_MAPPING:
                logger.warning(f"[ASSIGN] Model '{model_name}' NOT FOUND in mapping.")
                continue

            app_label = MODEL_MAPPING[model_name]

            try:
                model_class = ContentType.objects.get(
                    app_label=app_label, model=model_name
                ).model_class()
            except Exception as e:
                logger.error(
                    f"[ASSIGN] Could not load ContentType for {app_label}.{model_name}: {e}"
                )
                continue

            for perm_codename, obj_ids in perms_dict.items():
                for obj_id in obj_ids:
                    try:
                        obj = model_class.objects.get(id=obj_id)
                        assign_perm(perm_codename, group, obj)
                    except model_class.DoesNotExist:
                        logger.warning(
                            f"[ASSIGN] Object not found: {model_name}({obj_id})"
                        )
                    except Exception as e:
                        logger.error(
                            f"[ASSIGN] ERROR assigning '{perm_codename}' to {model_name}({obj_id}): {e}"
                        )

    # -------------------------------
    # REVOKE
    # -------------------------------
    if "revoke" in permissions:
        for model_name, perms_dict in permissions["revoke"].items():
            if model_name not in MODEL_MAPPING:
                logger.warning(f"[REVOKE] Model '{model_name}' NOT FOUND in mapping.")
                continue

            app_label = MODEL_MAPPING[model_name]

            try:
                model_class = ContentType.objects.get(
                    app_label=app_label, model=model_name
                ).model_class()
            except Exception as e:
                logger.error(
                    f"[REVOKE] Could not load ContentType for {app_label}.{model_name}: {e}"
                )
                continue

            for perm_codename, obj_ids in perms_dict.items():
                for obj_id in obj_ids:
                    try:
                        obj = model_class.objects.get(id=obj_id)
                        remove_perm(perm_codename, group, obj)
                    except model_class.DoesNotExist:
                        logger.warning(
                            f"[REVOKE] Object not found: {model_name}({obj_id})"
                        )
                    except Exception as e:
                        logger.error(
                            f"[REVOKE] ERROR removing '{perm_codename}' from {model_name}({obj_id}): {e}"
                        )

    logger.info("Bulk permission changes processed.")
