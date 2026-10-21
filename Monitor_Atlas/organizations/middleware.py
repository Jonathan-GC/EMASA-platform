from django.http import JsonResponse
from django.db.models import Q
from loguru import logger
from .models import Tenant
from roles.models import WorkspaceMembership


NON_TENANT_SCOPED_PATH_PREFIXES = (
    "/admin/",
    "/api/schema/",
    "/media/",
    "/api/v1/token/",
    "/api/v1/logout/",
    "/api/v1/csrf/",
    "/api/v1/system/",
    "/api/v1/users/auth/",
    "/api/v1/users/sessions/",
    "/api/v1/notifications/",
    "/api/v1/organizations/subscription/",
)

NON_TENANT_SCOPED_EXACT_PATHS = (
    "/api/v1/users/user/me/",
    "/api/v1/users/user/me",
)


def is_non_tenant_scoped_request(request) -> bool:
    """
    Determines if a request targets a non-tenant scoped endpoint where
    tenant context (X-Tenant-ID) is neither required nor enforced.
    """
    path = getattr(request, "path_info", None) or getattr(request, "path", "") or ""
    normalized_path = path if path.endswith("/") else f"{path}/"

    for prefix in NON_TENANT_SCOPED_PATH_PREFIXES:
        if path.startswith(prefix) or normalized_path.startswith(prefix):
            return True

    for exact in NON_TENANT_SCOPED_EXACT_PATHS:
        if path == exact or normalized_path == exact:
            return True

    # Tenant onboarding creation: POST /api/v1/organizations/tenant/
    method = getattr(request, "method", "") or ""
    if method.upper() == "POST" and (
        path in ("/api/v1/organizations/tenant/", "/api/v1/organizations/tenant")
        or normalized_path == "/api/v1/organizations/tenant/"
    ):
        return True

    return False


class TenantContextMiddleware:
    """
    Middleware that resolves the active tenant context for incoming HTTP requests.
    Clients may specify an 'X-Tenant-ID' header to switch tenant scope.
    If 'X-Tenant-ID' is absent, defaults to request.user.tenant.
    Non-tenant scoped endpoints bypass X-Tenant-ID validation and enforcement.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def _resolve_user(self, request):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            force_user = getattr(request, "_force_auth_user", None)
            if force_user and force_user.is_authenticated:
                user = force_user
                request.user = user
            else:
                try:
                    from rest_framework_simplejwt.authentication import JWTAuthentication
                    auth_res = JWTAuthentication().authenticate(request)
                    if auth_res:
                        user, _ = auth_res
                        request.user = user
                except Exception:
                    pass
        return user

    def __call__(self, request):
        # Exclude non-tenant scoped endpoints from X-Tenant-ID validation/enforcement
        if is_non_tenant_scoped_request(request):
            user = self._resolve_user(request)
            request.tenant = getattr(user, "tenant", None) if user and user.is_authenticated else None
            return self.get_response(request)

        tenant_id = None
        if hasattr(request, "headers"):
            tenant_id = request.headers.get("X-Tenant-ID")
        if not tenant_id and hasattr(request, "META"):
            tenant_id = request.META.get("HTTP_X_TENANT_ID")

        if tenant_id:
            tenant_id = tenant_id.strip()

        if tenant_id:
            target_tenant = Tenant.objects.filter(
                Q(id=tenant_id) | Q(cs_tenant_id=tenant_id)
            ).first()
            if not target_tenant:
                return JsonResponse({"detail": "Tenant not found."}, status=404)

            user = self._resolve_user(request)
            if not user or not user.is_authenticated:
                return JsonResponse(
                    {"detail": "Access to requested tenant is forbidden."}, status=403
                )

            is_authorized = False
            if user.is_superuser:
                is_authorized = True
            elif getattr(user, "tenant", None) and user.tenant.is_global:
                is_authorized = True
            elif getattr(user, "tenant", None) and str(user.tenant.id) == str(target_tenant.id):
                is_authorized = True
            elif WorkspaceMembership.objects.filter(
                user=user, workspace__tenant=target_tenant
            ).exists():
                is_authorized = True

            # Hall pass holders may access the target tenant even without
            # a WorkspaceMembership — the pass itself is the authorization.
            if not is_authorized:
                from django.utils import timezone as _tz
                from support.models import SupportHallPass
                if SupportHallPass.objects.filter(
                    technician=user,
                    workspace__tenant=target_tenant,
                    status__in=["ACTIVE", "active"],
                    expires_at__gt=_tz.now(),
                ).exists():
                    is_authorized = True

            if not is_authorized:
                logger.warning(
                    f"User {user.username} denied access to tenant {target_tenant.id} ({target_tenant.name})"
                )
                return JsonResponse(
                    {"detail": "Access to requested tenant is forbidden."}, status=403
                )

            request.tenant = target_tenant
        else:
            user = self._resolve_user(request)
            if user and user.is_authenticated:
                request.tenant = getattr(user, "tenant", None)
            else:
                request.tenant = None

        return self.get_response(request)

