from rest_framework.permissions import BasePermission
from .models import PermissionKey

def has_permission(user, scope, action, obj=None):
    """
    Check if a user has permission to perform an action on an object.

    This function is used by the HasPermissionKey permission class
    to check if a user has permission to perform an action on an object.

    Args:
        user: The user to check.
        scope: The scope of the action.
        action: The action to check.
        obj: The object to check (optional).

    Returns:
        True if the user has permission, False otherwise.
    """
    if not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    try:
        role = getattr(user.workspacemembership, 'role', None)
        if role is None:
            return False
        
        keys = PermissionKey.objects.filter(
            rolepermission__role=role,
            scope=scope,
            key_type=action
        )
    except AttributeError:
        return False

    for key in keys:
        
        if key.scope == scope and key.key_type == action:
            # If the scope is "node", "machine", "service", "user", or "role", check if the object has the corresponding ID
            if obj:
                match scope:
                    case "node":
                        if key.node_id == getattr(obj, 'id', None):
                            return True
                    case "machine":
                        if key.machine_id == getattr(obj, 'id', None):
                            return True
                    case "service":
                        if key.service_id == getattr(obj, 'id', None):
                            return True
                    case "user":
                        if key.user_id == getattr(obj, 'id', None):
                            return True
                    case "role":
                        if key.role_id == getattr(obj, 'id', None):
                            return True
            elif not any([key.node_id, key.machine_id, key.service_id, key.user_id, key.role_id]):
                return True
            else:
                return False
            


    return False


class HasPermissionKey(BasePermission):
    """
    Custom permission class that checks if a user has the required permission key
    for a given scope and action, optionally considering a specific object.
    """
    def has_permission(self, request, view):
        action = PermissionKey.from_view_action(view.action)
        scope = getattr(view, 'scope', None)
        user = request.user

        if not action:
            return False

        # Only call get_object if the action is a detail action
        obj = None
        if hasattr(view, 'get_object') and getattr(view, 'detail', False):
            try:
                obj = view.get_object()
            except Exception:
                obj = None
    
        return has_permission(user, scope, action, obj)

