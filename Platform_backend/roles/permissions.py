from rest_framework.permissions import BasePermission, SAFE_METHODS
from .models import PermissionKey
import logging

logger = logging.getLogger(__name__)


def has_permission(user, scope, action, obj=None):

    logger.warning(f"Checking perm: user={user}, scope={scope}, action={action}, obj={obj}")

    if not user.is_authenticated or not user.workspacemembership_set:
        logger.warning("User not authenticated")
        return False

    if user.is_superuser:
        logger.warning("No workspace membership found")
        return True

    membership = user.workspacemembership_set.first()
    if not membership:
        return False
    role = membership.role

    if isinstance(action, list):
        keys = PermissionKey.objects.filter(
            rolepermissions__role=role,
            scope=scope,
            key_type__in=action
        )
    else:
        keys = PermissionKey.objects.filter(
            rolepermissions__role=role,
            scope=scope,
            key_type=action
        )
    
    logger.warning(f"Found keys: {list(keys)}") 
    group = user.groups.first()

    is_internal = getattr(group, "name", None) == "EMASA"

    valid_actions = action if isinstance(action, list) else [action]

    for key in keys:
        if key.scope == scope and key.key_type in valid_actions:
            logger.warning(f"Checking key: {key}")
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
                    return True
            elif not any(
                [
                    key.node,
                    key.machine,
                    key.service,
                    key.user,
                    key.role,
                    key.workspace,
                    key.organization,
                    key.region,
                ]
            ):
                return True
    return False


class HasPermissionKey(BasePermission):
    """
    Custom permission class that checks if a user has the required permission key
    for a given scope and action, optionally considering a specific object.
    """

    def has_permission(self, request, view):
        action = PermissionKey.from_view_action(view.action)
        if not action:
            return False
        
        scope = getattr(view, "scope", None)
        user = request.user

        if not action:
            return False

        # Only call get_object if the action is a detail action
        obj = None
        if hasattr(view, "get_object") and getattr(view, "detail", False):
            try:
                obj = view.get_object()
            except Exception:
                obj = None

        return has_permission(user, scope, action, obj)


class IsAdminOrIsAuthenticatedReadOnly(BasePermission):
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
            return False

        if user.is_superuser:
            return True

        if request.method in SAFE_METHODS:
            return True

        return False
