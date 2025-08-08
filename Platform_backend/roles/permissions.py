from rest_framework.permissions import BasePermission, SAFE_METHODS
from .models import PermissionKey
import logging

ADMIN_SCOPES = ["permission_key", "role", "workspace"]

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

    if not user.is_authenticated or not user.workspacemembership_set.exists():
        logger.warning("User not authenticated or has no workspace memberships")
        return False

    if user.is_superuser:
        logger.warning("User is superuser, granting permission")
        return True

    membership = user.workspacemembership_set.first()
    if not membership:
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

    if not is_internal and obj:
        obj_org = getattr(getattr(obj, "workspace", None), "organization", None)
        if obj_org and obj_org != membership.workspace.organization:
            logger.warning("Organization mismatch")
            return False

    if membership.role.is_admin and scope in ADMIN_SCOPES:
        logger.warning("User is admin, granting permission")
        return True

    valid_actions = action if isinstance(action, list) else [action]

    for key in keys:
        if key.scope == scope and key.key_type in valid_actions:
            logger.warning(f"Checking key: {key.code}")
            parts = key.code.split(":")
            if obj:
                if any(
                    [
                        key.node_id == getattr(obj, "id", None),
                        key.machine_id == getattr(obj, "id", None),
                        key.service_id == getattr(obj, "id", None),
                        key.user_id == getattr(obj, "id", None),
                        key.role_id == getattr(obj, "id", None),
                        (
                            key.workspace_id == getattr(obj, "id", None)
                            if is_internal
                            else False
                        ),
                        (
                            key.organization_id == getattr(obj, "id", None)
                            if is_internal
                            else False
                        ),
                        (
                            key.region_id == getattr(obj, "id", None)
                            if is_internal
                            else False
                        ),
                    ]
                ):
                    logger.warning("User has permission based on object")
                    return True
            # If the permission key code is in the format 'scope:*:action', it grants permission for all objects in that scope and action.
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
