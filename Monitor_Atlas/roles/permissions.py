from rest_framework.permissions import BasePermission, SAFE_METHODS
from .models import PermissionKey
import logging

TENANT_ADMIN_SCOPES = ["role", "workspace", "role_permission"]

logger = logging.getLogger(__name__)


def has_permission(user, scope, action, obj=None):
    """
    Checks if a user has the given permission.

    Args:
        user (User): The user to check.
        scope (str): The scope of the permission.
        action (str or list): The action(s) of the permission.
        obj (any): The object related to the permission.

    Returns:
        bool: True if the user has permission, False otherwise.
    """
    logger.warning(
        f"Checking perm: user={user}, scope={scope}, action={action}, obj={obj}"
    )

    if user.is_superuser:
        # Superuser allways has permission
        logger.warning("User is superuser, granting permission")
        return True

    if not user.is_authenticated:
        logger.warning("User is not authenticated")
        return False

    membership = user.workspacemembership_set.first()

    if not membership:
        # User must have a workspace membership
        logger.warning("User has no workspace memberships")
        return False

    role = membership.role

    if isinstance(action, list):
        keys = PermissionKey.objects.filter(
            rolepermissions__role=role, scope=scope, key_type__in=action
        )
    else:
        keys = PermissionKey.objects.filter(
            rolepermissions__role=role, scope=scope, key_type=action
        )

    logger.warning(f"Found keys: {list(keys)}")
    # Get the first group of the user, or None if the user has no groups
    group = user.groups.first()

    is_internal = getattr(group, "name", None) == "EMASA"
    admin_status = membership.role.is_admin

    if not is_internal and obj:
        # Check if the object is in the same organization as the user, if not from EMASA
        try:
            obj_org = getattr(getattr(obj, "workspace", None), "organization", None)
        except Exception as e:
            logger.exception(f"Exception occurred while getting organization: {e}")
            obj_org = None
        if obj_org and obj_org != membership.workspace.organization:
            logger.warning("Organization mismatch")
            return False

    if admin_status and scope in TENANT_ADMIN_SCOPES:
        # Tenant (EMASA included) admin has permissions, see TENANT_ADMIN_SCOPES for details
        logger.warning("User is a tenant admin, granting permission")
        return True

    valid_actions = action if isinstance(action, list) else [action]

    for key in keys:
        # Check each found key
        if key.scope == scope and key.key_type in valid_actions:
            # Check if the key is valid
            logger.warning(f"Checking key: {key.code}")
            parts = key.code.split(":")
            if obj:
                # Check if the object matches the key
                if any(
                    [
                        key.device_id == getattr(obj, "id", None),
                        key.gateway_id == getattr(obj, "id", None),
                        key.machine_id == getattr(obj, "id", None),
                        key.application_id == getattr(obj, "id", None),
                        key.user_id == getattr(obj, "id", None),
                        key.role_id == getattr(obj, "id", None),
                        (
                            key.workspace_id == getattr(obj, "id", None)
                            if admin_status
                            else False
                        ),
                        (
                            key.tenant_id == getattr(obj, "id", None)
                            if is_internal
                            else False
                        ),
                        (
                            key.location_id == getattr(obj, "id", None)
                            if is_internal
                            else False
                        ),
                        (
                            key.device_profile_id == getattr(obj, "id", None)
                            if is_internal
                            else False
                        ),
                        (
                            key.device_profile_template_id == getattr(obj, "id", None)
                            if is_internal
                            else False
                        ),
                        (
                            key.api_user_id == getattr(obj, "id", None)
                            if is_internal
                            else False
                        ),
                        (
                            key.type_id == getattr(obj, "id", None)
                            if is_internal
                            else False
                        ),
                    ]
                ):
                    logger.warning("User has permission based on object")
                    # At this point the user has permission based on the object
                    return True
            # If the permission key code is in the format 'scope:*:action', it grants permission for all objects in that scope and action. (rarely used)
            elif len(parts) == 3 and parts[1] == "*":
                logger.warning("User has global permission based on scope and action")
                return True
    logger.warning("User does not have permission")
    return False


class HasPermissionKey(BasePermission):
    """
    Custom permission class that checks if a user has the required permission key
    for a given scope and action, optionally considering a specific object.
    """

    def has_permission(self, request, view):
        action_value = getattr(view, "action", None)
        print(f"Action value: {action_value}")

        action = PermissionKey.from_view_action(action_value)
        if not action:
            logger.warning(f"Invalid action: {action_value}")
            return False

        scope = getattr(view, "scope", None)
        user = request.user
        # Only call get_object if the action is a detail action.
        # The 'detail' attribute may not be present on all views; default to False if missing.
        obj = None
        if hasattr(view, "get_object") and getattr(view, "detail", False):
            try:
                obj = view.get_object()
            except Exception as e:
                logger.exception(
                    f"Exception occurred while getting object in view: {e}"
                )
                obj = None

        return has_permission(user, scope, action, obj)


class IsAdminOrIsAuthenticatedReadOnly(BasePermission):
    """
    Permission class that allows access to authenticated users for safe (read-only) methods,
    and grants full access to superusers for all methods.
    This permission is intended for automatic models such as permission keys or super-admin purposes.
    """

    def has_permission(self, request, view):
        """
        Returns True if the user has permission to access the view based on the
        request method and the user's authentication status. The permission rules
        are as follows:
        - GET, HEAD, OPTIONS requests are allowed if the user is authenticated.
        - POST, PUT, PATCH, DELETE requests are allowed if the user is a superuser.
        Otherwise, the method returns False.
        """
        user = request.user

        if not user.is_authenticated:
            logger.warning("User is not authenticated")
            return False

        if user.is_superuser:
            logger.warning("User is a superuser")
            return True

        if request.method in SAFE_METHODS:
            return True

        return False
