from rest_framework.permissions import BasePermission, SAFE_METHODS
from loguru import logger
from guardian.shortcuts import get_objects_for_user

from platform_backend import settings


def has_permission(user, perm, obj=None):
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
    logger.warning(f"Checking perm: user={user}, perm={perm}, obj={obj}")

    if not user.is_authenticated:
        logger.warning("User is not authenticated")
        return False

    if user.is_superuser:
        # Superuser allways has permission
        logger.warning("User is superuser, granting permission")
        return True

    has_perm = user.has_perm(perm, obj)
    logger.warning(f"Global permission check result: {has_perm}")

    return has_perm


def get_objects_for_user_and_workspace(user, perm, model_class, workspace=None):
    if user.is_superuser:
        return model_class.objects.all()
    else:
        queryset = get_objects_for_user(
            user, perm, klass=model_class, accept_global_perms=True
        )

    if workspace and hasattr(model_class, "workspace"):
        queryset = queryset.filter(workspace=workspace)
    return queryset


class HasPermission(BasePermission):
    """
    Permission class that checks if a user has the given permission.
    """

    def has_permission(self, request, view):
        """
        Returns True if the user has permission to access the view based on the
        provided scope and action. Otherwise, returns False.
        """
        user = request.user

        if not user.is_authenticated:
            logger.debug("User not authenticated")
            return False

        if user.is_superuser:
            logger.debug("Superuser access granted")
            return True

        scope = getattr(view, "scope", None)
        if not scope:
            logger.warning(f"View {view.__class__.__name__} missing scope")
            return False

        action = request.method.lower()

        logger.debug(f"Checking permission for action: {action} on scope: {scope}")

        perm_map = {
            "get": f"view_{scope}",
            "head": f"view_{scope}",
            "options": f"view_{scope}",
            "post": f"add_{scope}",
            "put": f"change_{scope}",
            "patch": f"change_{scope}",
            "delete": f"delete_{scope}",
        }

        perm_name = perm_map.get(action)
        if not perm_name:
            logger.warning(f"No permission mapping for action: {action}")
            return False

        if action == "get" and (view.action == "list" or view.action != "retrieve"):
            logger.debug("List action allowed")
            return True

        if action == "post":
            app_label = view.__class__.__module__.split(".")[0]
            full_perm = f"{app_label}.{perm_name}"
            has_perm = user.has_perm(full_perm)
            logger.debug(f"Global permission check for {full_perm}: {has_perm}")
            return has_perm

        if view.action in ["retrieve", "update", "partial_update", "destroy"]:
            logger.debug(
                f"Object-level action {view.action}, delegating to has_object_permission"
            )
            return True

        logger.warning(f"Unhandled action: {view.action}")
        return False

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.is_superuser:
            logger.debug("Superuser object access granted")
            return True

        scope = getattr(view, "scope", None)
        if not scope:
            logger.warning(f"View {view.__class__.__name__} missing scope")
            return False

        action = request.method.lower()
        perm_map = {
            "get": f"view_{scope}",
            "head": f"view_{scope}",
            "options": f"view_{scope}",
            "put": f"change_{scope}",
            "patch": f"change_{scope}",
            "delete": f"delete_{scope}",
        }

        perm_name = perm_map.get(action)
        if not perm_name:
            logger.warning(f"No permission mapping for action: {action}")
            return False

        has_perm = user.has_perm(perm_name, obj)
        logger.debug(f"Object permission check for {perm_name}: {has_perm}")
        return has_perm


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

        return request.method in SAFE_METHODS


# Support permissions can be added here in the future


class IsServiceOrHasPermission(BasePermission):
    def has_permission(self, request, view):
        api_key = request.headers.get("X-API-Key")
        if api_key and api_key == settings.SERVICE_API_KEY:
            return True
        has_perm_checker = HasPermission()
        return has_perm_checker.has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        api_key = request.headers.get("X-Service-API-Key")
        if api_key and api_key == settings.SERVICE_API_KEY:
            return True
        has_perm_checker = HasPermission()
        return has_perm_checker.has_object_permission(request, view, obj)
