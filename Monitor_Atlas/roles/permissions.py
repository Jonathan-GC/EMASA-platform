from rest_framework.permissions import BasePermission, SAFE_METHODS
from guardian.shortcuts import get_objects_for_user
from django_tenants.utils import get_tenant
from loguru import logger


def get_current_tenant(request):
    """Helper to retrieve the current tenant"""
    try:
        return get_tenant(request)
    except:
        return None


def has_permission(user, perm, obj=None):
    """
    Check permissions using Guardian.

    Args:
        user: User
        perm: Permission in the format 'app_label.permission_name'
        obj: Optional object for object-level permissions

    Returns:
        bool: True if has permission
    """
    logger.debug(f"Checking perm: user={user}, perm={perm}, obj={obj}")

    # 1. Superuser always has permission
    if user.is_superuser:
        logger.debug("User is superuser, granting permission")
        return True

    # 2. User must be authenticated
    if not user.is_authenticated:
        logger.debug("User not authenticated")
        return False

    # 3. Check object permission with Guardian
    if obj:
        has_perm = user.has_perm(perm, obj)
        logger.debug(f"Object permission check: {has_perm}")
        return has_perm

    # 4. Check global permission
    has_perm = user.has_perm(perm)
    logger.debug(f"Global permission check: {has_perm}")
    return has_perm


def get_objects_for_user_and_workspace(user, perm, model_class, workspace=None):
    """
    Get objects the user can access in a workspace.

    Args:
        user: User
        perm: Permission (e.g., 'infrastructure.view_device')
        model_class: Model class
        workspace: Optional workspace to filter by

    Returns:
        QuerySet of accessible objects
    """
    if user.is_superuser:
        queryset = model_class.objects.all()
    else:
        # Guardian: get objects the user has permission for
        queryset = get_objects_for_user(
            user,
            perm,
            klass=model_class,
            accept_global_perms=True,
        )

    # Filter by workspace if provided
    if workspace and hasattr(model_class, "workspace"):
        queryset = queryset.filter(workspace=workspace)

    return queryset


class HasPermission(BasePermission):
    """
    Permission class based on Guardian.
    Replaces HasPermissionKey.
    """

    def has_permission(self, request, view):
        """Check global permission"""
        user = request.user

        if not user.is_authenticated:
            return False

        # Superuser has all permissions
        if user.is_superuser:
            return True

        # Get required scope from the view
        scope = getattr(view, "scope", None)
        if not scope:
            logger.warning(f"View {view.__class__.__name__} has no scope defined")
            return False

        # Map action to permission
        action = request.method.lower()
        perm_map = {
            "get": f"view_{scope}",
            "post": f"add_{scope}",
            "put": f"change_{scope}",
            "patch": f"change_{scope}",
            "delete": f"delete_{scope}",
        }

        perm_name = perm_map.get(action)
        if not perm_name:
            return False

        # Check global permission
        full_perm = f"{view.__class__.__module__.split('.')[0]}.{perm_name}"
        return user.has_perm(full_perm)

    def has_object_permission(self, request, view, obj):
        """Check object-specific permission"""
        user = request.user

        if user.is_superuser:
            return True

        scope = getattr(view, "scope", None)
        if not scope:
            return False

        # Map action to permission
        action = request.method.lower()
        perm_map = {
            "get": f"view_{scope}",
            "post": f"add_{scope}",
            "put": f"change_{scope}",
            "patch": f"change_{scope}",
            "delete": f"delete_{scope}",
        }

        perm_name = perm_map.get(action)
        if not perm_name:
            return False

        # Check object permission with Guardian
        full_perm = f"{obj._meta.app_label}.{perm_name}"
        return user.has_perm(full_perm, obj)


class IsAdminOrIsAuthenticatedReadOnly(BasePermission):
    """
    Permission for administrative endpoints.
    - Read: any authenticated user
    - Write: only superuser
    """

    def has_permission(self, request, view):
        user = request.user

        if not user.is_authenticated:
            return False

        if user.is_superuser:
            return True

        # Read-only for normal users
        return request.method in SAFE_METHODS
