from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.exceptions import PermissionDenied
from loguru import logger
from guardian.shortcuts import get_objects_for_user, get_perms
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import models

from .helpers import (
    get_global_admin_role_group,
    get_tenant_default_workspace,
    get_user_workspace_admin_status,
)


CUSTOM_ACTION_DECORATORS = [
    "set_activation",
    "create_measurement",
    "activate",
    "deactivate",
    "get_ws_link",
    "bulk_assign_permissions",
    "remove_user",
]

WORKSPACE_SCOPED_MODELS = {
    "device",
    "gateway",
    "application",
    "machine",
    "location",
    "deviceprofile",
    "apiuser",
    "role",
    "workspacemembership",
}

TENANT_SCOPED_MODELS = {
    "tenant",
    "workspace",
    "subscription",
}


def get_object_workspace_and_tenant(obj):
    """
    Extracts the workspace and tenant context from a target object,
    traversing hierarchical relationships if necessary.
    """
    if obj is None:
        return None, None

    from organizations.models import Tenant, Workspace

    if isinstance(obj, Tenant):
        return None, obj

    if isinstance(obj, Workspace):
        return obj, obj.tenant

    obj_workspace = getattr(obj, "workspace", None)
    obj_tenant = getattr(obj, "tenant", None)

    if obj_workspace is not None and obj_tenant is None:
        obj_tenant = getattr(obj_workspace, "tenant", None)

    # Hierarchical traversal for nested resources
    if obj_workspace is None:
        # Location -> Gateway -> Workspace
        if hasattr(obj, "gateway") and obj.gateway is not None:
            obj_workspace = getattr(obj.gateway, "workspace", None)
            if obj_workspace is not None and obj_tenant is None:
                obj_tenant = getattr(obj_workspace, "tenant", None)

        # Measurement -> Device -> Workspace
        elif hasattr(obj, "device") and obj.device is not None:
            obj_workspace = getattr(obj.device, "workspace", None)
            if obj_workspace is not None and obj_tenant is None:
                obj_tenant = getattr(obj_workspace, "tenant", None)

        # CommentAttachment -> Comment -> Ticket
        elif hasattr(obj, "comment") and obj.comment is not None:
            comment = obj.comment
            ticket = getattr(comment, "ticket", None)
            if ticket is not None:
                obj_workspace = getattr(ticket, "workspace", None)
                obj_tenant = getattr(ticket, "tenant", None) or getattr(ticket, "organization", None)
                if obj_tenant is None and hasattr(ticket, "user") and ticket.user is not None:
                    obj_tenant = getattr(ticket.user, "tenant", None)
                if obj_workspace is not None and obj_tenant is None:
                    obj_tenant = getattr(obj_workspace, "tenant", None)

        # Comment -> Ticket -> Tenant / Organization
        # Attachment -> Ticket -> Tenant / Organization
        elif hasattr(obj, "ticket") and obj.ticket is not None:
            ticket = obj.ticket
            obj_workspace = getattr(ticket, "workspace", None)
            obj_tenant = getattr(ticket, "tenant", None) or getattr(ticket, "organization", None)
            if obj_tenant is None and hasattr(ticket, "user") and ticket.user is not None:
                obj_tenant = getattr(ticket.user, "tenant", None)
            if obj_workspace is not None and obj_tenant is None:
                obj_tenant = getattr(obj_workspace, "tenant", None)

        # Ticket -> Organization / User tenant fallback
        elif hasattr(obj, "organization") and obj.organization is not None:
            if obj_tenant is None:
                obj_tenant = obj.organization

    if obj_tenant is None and hasattr(obj, "user") and obj.user is not None:
        obj_tenant = getattr(obj.user, "tenant", None)

    return obj_workspace, obj_tenant


def has_contextual_perm(
    user,
    perm: str,
    tenant=None,
    workspace=None,
    obj=None,
) -> bool:
    """
    Evaluates user permissions strictly within active (tenant, workspace) context.
    Eliminates cross-tenant and cross-workspace leakage by querying active
    WorkspaceMembership.role.group and Guardian object permissions rather
    than flat Django user.groups.
    """
    if not user or not user.is_authenticated:
        logger.debug("Contextual perm check failed: user is not authenticated")
        return False

    if user.is_superuser:
        logger.debug(f"Superuser contextual bypass for user={user.username}")
        return True

    # Check for global administrator bypass
    user_tenant = getattr(user, "tenant", None)
    if user_tenant and getattr(user_tenant, "is_global", False):
        global_group = get_global_admin_role_group()
        from roles.models import WorkspaceMembership
        is_global_admin = (
            (global_group and global_group in user.groups.all())
            or user.groups.filter(name="global_admin").exists()
            or WorkspaceMembership.objects.filter(
                user=user,
                workspace__tenant__is_global=True,
                role__name__icontains="admin",
            ).exists()
        )
        if is_global_admin:
            try:
                from auditlog.models import LogEntry
                target_ct = (
                    ContentType.objects.get_for_model(obj.__class__)
                    if obj is not None
                    else ContentType.objects.get_for_model(user.__class__)
                )
                target_pk = str(obj.pk) if obj is not None else str(user.pk)
                target_repr = str(obj) if obj is not None else str(user)
                LogEntry.objects.create(
                    content_type=target_ct,
                    object_pk=target_pk,
                    object_repr=target_repr,
                    action=LogEntry.Action.ACCESS,
                    actor=user,
                    additional_data={
                        "action_detail": "global_admin_bypass",
                        "perm": perm,
                        "target_tenant": str(tenant.id) if tenant else None,
                        "target_workspace": str(workspace.id) if workspace else None,
                    },
                )
            except Exception as audit_err:
                logger.debug(f"Audit log recording for global admin bypass: {audit_err}")
            return True

    codename = perm.split(".")[-1] if "." in perm else perm
    app_label = perm.split(".")[0] if "." in perm else None

    # Check for global support manager bypass on support resources
    support_domains = ("ticket", "comment", "attachment", "commentattachment", "supportmembership", "technicianassignment")
    if any(s in codename for s in support_domains):
        from support.models import SupportMembership
        is_global_support_mgr = SupportMembership.objects.filter(
            user=user, role="support_manager"
        ).filter(models.Q(tenant__is_global=True) | models.Q(tenant__isnull=True)).exists()
        if is_global_support_mgr:
            return True

    # Resolve context from object if missing
    obj_ws, obj_t = get_object_workspace_and_tenant(obj)
    if workspace is None and obj_ws is not None:
        workspace = obj_ws
    if tenant is None and obj_t is not None:
        tenant = obj_t

    # Check active valid TechnicianAssignment pass on workspace
    has_active_diagnostic_pass = False
    if workspace is not None:
        from django.utils import timezone
        from support.models import TechnicianAssignment

        has_active_diagnostic_pass = TechnicianAssignment.objects.filter(
            technician=user,
            workspace=workspace,
            status__in=["ACTIVE", "active"],
            expires_at__gt=timezone.now(),
        ).exists()

    # Assigned technician check
    is_assigned_technician = False
    if obj is not None:
        if hasattr(obj, "assigned_to") and obj.assigned_to == user:
            is_assigned_technician = True
        elif hasattr(obj, "ticket") and getattr(obj.ticket, "assigned_to", None) == user:
            is_assigned_technician = True
        elif hasattr(obj, "comment") and hasattr(obj.comment, "ticket") and getattr(obj.comment.ticket, "assigned_to", None) == user:
            is_assigned_technician = True

    # Validate object boundary against active context
    if obj is not None:
        if workspace is not None and obj_ws is not None and str(obj_ws.id) != str(workspace.id):
            if not is_assigned_technician:
                logger.warning(
                    f"Contextual boundary violation: obj.workspace={obj_ws.id} does not match active workspace={workspace.id}"
                )
                return False
        if tenant is not None and obj_t is not None and str(obj_t.id) != str(tenant.id):
            if not is_assigned_technician and not has_active_diagnostic_pass:
                logger.warning(
                    f"Contextual boundary violation: obj.tenant={obj_t.id} does not match active tenant={tenant.id}"
                )
                return False

    # Assigned technician permissions on ticket/comment/attachment
    if is_assigned_technician:
        if codename in [
            "view_ticket",
            "change_ticket",
            "view_comment",
            "add_comment",
            "change_comment",
            "view_attachment",
            "add_attachment",
            "view_commentattachment",
            "add_commentattachment",
        ]:
            return True

    # Workspace-level contextual evaluation
    if workspace is not None:
        # Diagnostic pass grants read-only SAFE_METHODS (view_*)
        if has_active_diagnostic_pass and codename.startswith("view_"):
            logger.debug(
                f"Diagnostic pass granted for user={user.username} on workspace={workspace.id} for perm={codename}"
            )
            return True

        from roles.models import WorkspaceMembership

        membership = (
            WorkspaceMembership.objects.filter(user=user, workspace=workspace)
            .select_related("role", "role__group")
            .first()
        )
        if not membership or not membership.role:
            logger.debug(
                f"User {user.username} has no active membership in workspace {workspace.id}"
            )
            return False

        role_group = membership.role.group
        if not role_group:
            return False

        # Model-level permission granted to the role group
        if app_label:
            has_group_perm = role_group.permissions.filter(
                content_type__app_label=app_label, codename=codename
            ).exists()
        else:
            has_group_perm = role_group.permissions.filter(codename=codename).exists()

        if has_group_perm and obj is None:
            return True

        # Object-level permission evaluation
        if obj is not None:
            has_obj_perm = (
                codename in get_perms(role_group, obj)
                or codename in get_perms(user, obj)
            )
            return has_group_perm or has_obj_perm

        return has_group_perm

    # Tenant-level contextual evaluation (when workspace is None)
    if tenant is not None:
        from roles.models import WorkspaceMembership

        # User must belong to the tenant or have membership in one of its workspaces
        if getattr(user, "tenant", None) != tenant:
            if not WorkspaceMembership.objects.filter(
                user=user, workspace__tenant=tenant
            ).exists():
                logger.debug(
                    f"User {user.username} has no affiliation with tenant {tenant.id}"
                )
                return False

        # Support subsystem permissions for tenant members
        if any(s in codename for s in ["ticket", "comment", "attachment"]):
            if obj is None:
                if codename in [
                    "view_ticket",
                    "add_ticket",
                    "view_comment",
                    "add_comment",
                    "view_attachment",
                    "add_attachment",
                    "view_commentattachment",
                    "add_commentattachment",
                ]:
                    return True
            else:
                if codename == "view_ticket":
                    return True
                if codename == "change_ticket":
                    has_perm = (
                        codename in get_perms(user, obj)
                        or user.user_permissions.filter(codename=codename).exists()
                        or WorkspaceMembership.objects.filter(
                            user=user, workspace__tenant=tenant
                        ).filter(
                            models.Q(role__is_admin=True) | models.Q(role__name__icontains="admin")
                        ).exists()
                    )
                    return has_perm

        # Check direct user permissions or guardian perms
        if obj is not None:
            return codename in get_perms(user, obj)

        if app_label:
            return user.user_permissions.filter(
                content_type__app_label=app_label, codename=codename
            ).exists()
        return user.user_permissions.filter(codename=codename).exists()

    logger.debug("No contextual boundary resolved (neither workspace nor tenant provided)")
    return False


def has_permission(user, perm, obj=None):
    """
    Backward-compatible global permission evaluator wrapping has_contextual_perm.
    """
    return has_contextual_perm(user, perm, obj=obj)


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


class HasContextualPermission(BasePermission):
    """
    Context-aware permission class for Django REST Framework.
    Resolves active tenant (via request.tenant) and active workspace
    (via X-Workspace-ID header, query param, or object context),
    enforcing action mapping, object ownership boundaries, and zero leakage.
    """

    @staticmethod
    def _get_service_api_key(request):
        if hasattr(request, "headers"):
            return request.headers.get("X-Service-API-Key") or request.headers.get("X-API-Key")
        if hasattr(request, "META"):
            return request.META.get("HTTP_X_SERVICE_API_KEY") or request.META.get("HTTP_X_API_KEY")
        return None

    def _resolve_workspace(self, request, view):
        from organizations.models import Workspace

        ws_id = None
        if hasattr(request, "headers"):
            ws_id = request.headers.get("X-Workspace-ID")
        if not ws_id and hasattr(request, "META"):
            ws_id = request.META.get("HTTP_X_WORKSPACE_ID")
        if not ws_id and hasattr(request, "query_params"):
            ws_id = request.query_params.get("workspace") or request.query_params.get("workspace_id")
        if not ws_id and hasattr(request, "data") and isinstance(request.data, dict):
            ws_id = request.data.get("workspace") or request.data.get("workspace_id")
        if not ws_id and hasattr(view, "kwargs"):
            ws_id = view.kwargs.get("workspace_pk") or view.kwargs.get("workspace_id")

        if ws_id:
            try:
                ws = Workspace.objects.get(id=ws_id)
                request.workspace = ws
                return ws
            except (Workspace.DoesNotExist, ValueError):
                raise PermissionDenied("Specified workspace was not found.")

        request.workspace = getattr(request, "workspace", None)
        return request.workspace

    def has_permission(self, request, view):
        # 1. Internal Service API Key bypass
        api_key = self._get_service_api_key(request)
        if api_key and hasattr(settings, "SERVICE_API_KEY") and api_key == settings.SERVICE_API_KEY:
            return True

        user = request.user
        if not user or not user.is_authenticated:
            return False

        if user.is_superuser:
            return True

        if getattr(view, "action", None) == "me":
            return True

        scope = getattr(view, "scope", None)
        if not scope:
            logger.warning(f"View {view.__class__.__name__} missing required 'scope'")
            return False

        # Active tenant resolution (from TenantContextMiddleware or user)
        tenant = getattr(request, "tenant", None) or getattr(user, "tenant", None)
        request.tenant = tenant

        # Global admin cross-tenant bypass
        if getattr(user, "tenant", None) and user.tenant.is_global:
            global_group = get_global_admin_role_group()
            if (global_group and global_group in user.groups.all()) or user.groups.filter(name="global_admin").exists():
                return True

        # Active workspace resolution
        workspace = self._resolve_workspace(request, view)

        # Check for active diagnostic pass on workspace
        has_active_diagnostic_pass = False
        if workspace:
            from django.utils import timezone
            from support.models import TechnicianAssignment

            has_active_diagnostic_pass = TechnicianAssignment.objects.filter(
                technician=user,
                workspace=workspace,
                status__in=["ACTIVE", "active"],
                expires_at__gt=timezone.now(),
            ).exists()

        if has_active_diagnostic_pass:
            tenant = workspace.tenant
            request.tenant = tenant
            if request.method.lower() not in ["get", "head", "options"] and scope not in [
                "ticket", "comment", "attachment", "commentattachment", "supportmembership", "technicianassignment"
            ]:
                from roles.models import WorkspaceMembership
                if not WorkspaceMembership.objects.filter(user=user, workspace=workspace).exists():
                    raise PermissionDenied("Diagnostic pass grants read-only access only.")

        # Global support manager cross-tenant bypass on support resources
        if scope in ["ticket", "comment", "attachment", "commentattachment", "supportmembership", "technicianassignment"]:
            from support.models import SupportMembership
            from django.db.models import Q
            is_global_support_mgr = SupportMembership.objects.filter(
                user=user, role="support_manager"
            ).filter(Q(tenant__is_global=True) | Q(tenant__isnull=True)).exists()
            if is_global_support_mgr:
                return True

        # Validate tenant boundary on resolved workspace
        if workspace and tenant and getattr(workspace, "tenant_id", None) != tenant.id:
            if not has_active_diagnostic_pass:
                raise PermissionDenied("Active workspace does not belong to active tenant.")

        action = request.method.lower()
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
            logger.warning(f"No permission mapping for HTTP method {action}")
            return False

        # Custom action decorator overrides
        if hasattr(view, "action") and view.action in CUSTOM_ACTION_DECORATORS:
            if view.action in ["set_activation", "activate", "deactivate"]:
                perm_name = f"change_{scope}"
            elif view.action == "create_measurement":
                perm_name = "add_measurements"
            elif view.action in ["bulk_assign_permissions", "remove_user"]:
                perm_name = f"change_{scope}"

        # If operation is on a workspace-scoped resource, ensure context can be resolved
        if scope in WORKSPACE_SCOPED_MODELS:
            if workspace is None:
                # Detail actions can resolve context from object in has_object_permission
                if getattr(view, "action", None) in ["list", "create"]:
                    raise PermissionDenied(
                        f"Active workspace context (X-Workspace-ID or workspace parameter) is required for {scope} operations."
                    )

        # If operation is on a tenant-scoped resource, ensure tenant is resolved
        if scope in TENANT_SCOPED_MODELS and tenant is None:
            raise PermissionDenied("Active tenant context is required for this operation.")

        # Defer detail actions without explicit workspace context to has_object_permission
        is_detail_action = getattr(view, "detail", False) or getattr(view, "action", None) in [
            "retrieve",
            "update",
            "partial_update",
            "destroy",
            *CUSTOM_ACTION_DECORATORS,
        ]
        if is_detail_action and workspace is None:
            return True

        has_perm = has_contextual_perm(
            user=user,
            perm=perm_name,
            tenant=tenant,
            workspace=workspace,
        )
        if not has_perm:
            raise PermissionDenied(f"Contextual permission '{perm_name}' denied.")

        return True

    def has_object_permission(self, request, view, obj):
        api_key = self._get_service_api_key(request)
        if api_key and hasattr(settings, "SERVICE_API_KEY") and api_key == settings.SERVICE_API_KEY:
            return True

        user = request.user
        if not user or not user.is_authenticated:
            return False

        if user.is_superuser:
            return True

        scope = getattr(view, "scope", None)
        if not scope:
            return False

        tenant = getattr(request, "tenant", None) or getattr(user, "tenant", None)
        request.tenant = tenant

        if getattr(user, "tenant", None) and user.tenant.is_global:
            global_group = get_global_admin_role_group()
            if (global_group and global_group in user.groups.all()) or user.groups.filter(name="global_admin").exists():
                return True

        obj_ws, obj_t = get_object_workspace_and_tenant(obj)
        req_ws = getattr(request, "workspace", None)
        effective_ws = req_ws or obj_ws

        has_active_diagnostic_pass = False
        if effective_ws:
            from django.utils import timezone
            from support.models import TechnicianAssignment

            has_active_diagnostic_pass = TechnicianAssignment.objects.filter(
                technician=user,
                workspace=effective_ws,
                status__in=["ACTIVE", "active"],
                expires_at__gt=timezone.now(),
            ).exists()

        if has_active_diagnostic_pass and scope not in [
            "ticket", "comment", "attachment", "commentattachment", "supportmembership", "technicianassignment"
        ]:
            if request.method.lower() not in ["get", "head", "options"]:
                from roles.models import WorkspaceMembership
                if not WorkspaceMembership.objects.filter(user=user, workspace=effective_ws).exists():
                    raise PermissionDenied("Diagnostic pass grants read-only access only.")

        # Check assigned technician on ticket / comment / attachment
        is_assigned_technician = False
        if scope == "ticket" or hasattr(obj, "assigned_to"):
            is_assigned_technician = getattr(obj, "assigned_to", None) == user
        elif hasattr(obj, "ticket"):
            is_assigned_technician = getattr(obj.ticket, "assigned_to", None) == user
        elif hasattr(obj, "comment") and hasattr(obj.comment, "ticket"):
            is_assigned_technician = getattr(obj.comment.ticket, "assigned_to", None) == user

        is_global_support_mgr = False
        if scope in ["ticket", "comment", "attachment", "commentattachment", "supportmembership", "technicianassignment"]:
            from support.models import SupportMembership
            from django.db.models import Q
            is_global_support_mgr = SupportMembership.objects.filter(
                user=user, role="support_manager"
            ).filter(Q(tenant__is_global=True) | Q(tenant__isnull=True)).exists()

        if is_global_support_mgr:
            return True

        # Validate object boundary against active request context
        if req_ws and obj_ws and str(obj_ws.id) != str(req_ws.id):
            if not is_assigned_technician and not is_global_support_mgr:
                logger.warning(
                    f"Object boundary violation: obj.workspace={obj_ws.id} does not match request.workspace={req_ws.id}"
                )
                raise PermissionDenied("Object belongs to a different workspace.")

        if tenant and obj_t and str(obj_t.id) != str(tenant.id):
            if not is_assigned_technician and not is_global_support_mgr and not has_active_diagnostic_pass:
                logger.warning(
                    f"Object boundary violation: obj.tenant={obj_t.id} does not match request.tenant={tenant.id}"
                )
                raise PermissionDenied("Object belongs to a different tenant.")

        action = request.method.lower()
        perm_map = {
            "get": f"view_{scope}",
            "head": f"view_{scope}",
            "options": f"view_{scope}",
            "put": f"change_{scope}",
            "post": f"change_{scope}",
            "patch": f"change_{scope}",
            "delete": f"delete_{scope}",
        }

        perm_name = perm_map.get(action)
        if not perm_name:
            return False

        if is_assigned_technician:
            if perm_name in [
                "view_ticket",
                "change_ticket",
                "view_comment",
                "add_comment",
                "change_comment",
                "view_attachment",
                "add_attachment",
                "view_commentattachment",
                "add_commentattachment",
            ]:
                return True

        effective_ws = req_ws or obj_ws
        effective_tenant = tenant or obj_t

        has_perm = has_contextual_perm(
            user=user,
            perm=perm_name,
            tenant=effective_tenant,
            workspace=effective_ws,
            obj=obj,
        )
        if not has_perm:
            raise PermissionDenied(f"Object-level permission '{perm_name}' denied.")

        return True


# Backward-compatible alias
HasPermission = HasContextualPermission


class IsAnAdminUser(BasePermission):
    """
    Allows access only to admin users.
    """

    def has_permission(self, request, view):
        global_group = get_global_admin_role_group()

        return request.user.is_authenticated and (
            request.user.is_superuser or (global_group and global_group in request.user.groups.all())
        )


class IsTenantAdminUser(BasePermission):
    """
    Allows access only to tenant admin users.
    """

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        if user.is_superuser:
            return True

        tenant = getattr(user, "tenant", None)
        if not tenant:
            return False

        default_workspace = get_tenant_default_workspace(tenant)
        if not default_workspace:
            return False

        return get_user_workspace_admin_status(user, default_workspace)


class IsAdminOrIsAuthenticatedReadOnly(BasePermission):
    """
    Permission for administrative endpoints.
    - Read: any authenticated user
    - Write: only superuser
    """

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        if user.is_superuser:
            return True

        return request.method in SAFE_METHODS


class IsOwnerOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user and (request.user.is_staff or request.user.is_superuser):
            return True
        return getattr(obj, "user", None) == request.user


class IsServiceOrHasPermission(BasePermission):
    @staticmethod
    def _get_service_api_key(request):
        if hasattr(request, "headers"):
            return request.headers.get("X-API-Key") or request.headers.get("X-Service-API-Key")
        if hasattr(request, "META"):
            return request.META.get("HTTP_X_API_KEY") or request.META.get("HTTP_X_SERVICE_API_KEY")
        return None

    def has_permission(self, request, view):
        api_key = self._get_service_api_key(request)
        if api_key and hasattr(settings, "SERVICE_API_KEY") and api_key == settings.SERVICE_API_KEY:
            return True
        has_perm_checker = HasContextualPermission()
        return has_perm_checker.has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        api_key = self._get_service_api_key(request)
        if api_key and hasattr(settings, "SERVICE_API_KEY") and api_key == settings.SERVICE_API_KEY:
            return True
        has_perm_checker = HasContextualPermission()
        return has_perm_checker.has_object_permission(request, view, obj)
