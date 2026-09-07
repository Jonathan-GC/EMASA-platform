from django.http import JsonResponse
from loguru import logger
from .models import Tenant
from roles.models import WorkspaceMembership


class TenantContextMiddleware:
    """
    Middleware that resolves the active tenant context for incoming HTTP requests.
    Clients may specify an 'X-Tenant-ID' header to switch tenant scope.
    If 'X-Tenant-ID' is absent, defaults to request.user.tenant.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tenant_id = None
        if hasattr(request, "headers"):
            tenant_id = request.headers.get("X-Tenant-ID")
        if not tenant_id and hasattr(request, "META"):
            tenant_id = request.META.get("HTTP_X_TENANT_ID")

        if tenant_id:
            tenant_id = tenant_id.strip()

        if tenant_id:
            try:
                target_tenant = Tenant.objects.get(id=tenant_id)
            except Tenant.DoesNotExist:
                return JsonResponse({"detail": "Tenant not found."}, status=404)

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

            if not is_authorized:
                logger.warning(
                    f"User {user.username} denied access to tenant {target_tenant.id} ({target_tenant.name})"
                )
                return JsonResponse(
                    {"detail": "Access to requested tenant is forbidden."}, status=403
                )

            request.tenant = target_tenant
        else:
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

            if user and user.is_authenticated:
                request.tenant = getattr(user, "tenant", None)
            else:
                request.tenant = None

        return self.get_response(request)

