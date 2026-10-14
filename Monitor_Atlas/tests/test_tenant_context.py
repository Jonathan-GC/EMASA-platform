from django.test import TestCase, RequestFactory
from django.http import HttpResponse
from django.contrib.auth.models import AnonymousUser, Group
from rest_framework.test import APIClient
from rest_framework import status

from organizations.models import Tenant, Workspace, Subscription
from organizations.middleware import TenantContextMiddleware
from organizations.helpers import (
    get_or_create_default_workspace,
    get_or_create_admin_role,
    get_no_role,
    get_global_tenant,
)
from roles.models import Role, WorkspaceMembership
from users.models import User


class TenantContextMiddlewareTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.subscription = Subscription.objects.create(
            name="Context Test Plan",
            description="Subscription for context tests",
        )
        self.global_tenant = Tenant.objects.create(
            name="Global Master",
            subscription=self.subscription,
            is_global=True,
        )
        self.tenant_a = Tenant.objects.create(
            name="Tenant Alpha",
            subscription=self.subscription,
            is_global=False,
        )
        self.tenant_b = Tenant.objects.create(
            name="Tenant Beta",
            subscription=self.subscription,
            is_global=False,
        )

        self.ws_a = Workspace.objects.create(
            name="Workspace Alpha", tenant=self.tenant_a
        )
        self.ws_b = Workspace.objects.create(
            name="Workspace Beta", tenant=self.tenant_b
        )

        # Users
        self.user_a = User.objects.create_user(
            username="user_a",
            email="user_a@test.com",
            tenant=self.tenant_a,
        )
        self.role_a = get_no_role(self.ws_a)
        WorkspaceMembership.objects.create(
            workspace=self.ws_a, user=self.user_a, role=self.role_a
        )

        self.user_b = User.objects.create_user(
            username="user_b",
            email="user_b@test.com",
            tenant=self.tenant_b,
        )
        self.role_b = get_no_role(self.ws_b)
        WorkspaceMembership.objects.create(
            workspace=self.ws_b, user=self.user_b, role=self.role_b
        )

        self.superuser = User.objects.create_superuser(
            username="super_admin",
            email="super@test.com",
            tenant=self.global_tenant,
        )

        self.global_admin = User.objects.create_user(
            username="global_admin_user",
            email="global_admin@test.com",
            tenant=self.global_tenant,
        )

    def _get_middleware(self):
        return TenantContextMiddleware(lambda req: HttpResponse("OK"))

    def test_fallback_to_user_tenant_when_header_omitted(self):
        """When X-Tenant-ID is omitted, request.tenant falls back to user.tenant."""
        request = self.factory.get("/api/v1/organizations/workspaces/")
        request.user = self.user_a

        middleware = self._get_middleware()
        response = middleware(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(request.tenant, self.tenant_a)

    def test_valid_x_tenant_id_resolves_for_authorized_member(self):
        """When user is an active member of target tenant, X-Tenant-ID resolves correctly."""
        # Grant user_a a membership in tenant_b as well
        ws_b_extra = Workspace.objects.create(
            name="Shared WS in B", tenant=self.tenant_b
        )
        role_b_extra = get_no_role(ws_b_extra)
        WorkspaceMembership.objects.create(
            workspace=ws_b_extra, user=self.user_a, role=role_b_extra
        )

        request = self.factory.get(
            "/api/v1/organizations/workspaces/",
            HTTP_X_TENANT_ID=str(self.tenant_b.id),
        )
        request.user = self.user_a

        middleware = self._get_middleware()
        response = middleware(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(request.tenant, self.tenant_b)

    def test_valid_cs_tenant_id_resolves_for_authorized_member(self):
        """When user supplies ChirpStack UUID cs_tenant_id, it resolves correctly to the tenant."""
        self.tenant_b.cs_tenant_id = "52f14fb4-c713-433e-9f8d-037114fa33c8"
        self.tenant_b.save(update_fields=["cs_tenant_id"])

        ws_b_extra = Workspace.objects.create(
            name="Shared WS in B for CS ID", tenant=self.tenant_b
        )
        role_b_extra = get_no_role(ws_b_extra)
        WorkspaceMembership.objects.create(
            workspace=ws_b_extra, user=self.user_a, role=role_b_extra
        )

        request = self.factory.get(
            "/api/v1/organizations/workspaces/",
            HTTP_X_TENANT_ID="52f14fb4-c713-433e-9f8d-037114fa33c8",
        )
        request.user = self.user_a

        middleware = self._get_middleware()
        response = middleware(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(request.tenant, self.tenant_b)

    def test_unauthorized_x_tenant_id_yields_403(self):
        """When user lacks authorization for target tenant, X-Tenant-ID yields HTTP 403."""
        request = self.factory.get(
            "/api/v1/organizations/workspaces/",
            HTTP_X_TENANT_ID=str(self.tenant_b.id),
        )
        request.user = self.user_a

        middleware = self._get_middleware()
        response = middleware(request)

        self.assertEqual(response.status_code, 403)
        self.assertIn("forbidden", response.content.decode().lower())

    def test_nonexistent_x_tenant_id_yields_404(self):
        """When X-Tenant-ID specifies a non-existent ID, yields HTTP 404."""
        request = self.factory.get(
            "/api/v1/organizations/workspaces/",
            HTTP_X_TENANT_ID="nonexistent123456",
        )
        request.user = self.user_a

        middleware = self._get_middleware()
        response = middleware(request)

        self.assertEqual(response.status_code, 404)
        self.assertIn("not found", response.content.decode().lower())

    def test_global_administrator_context_switching_across_tenants(self):
        """Global administrator can switch context to any tenant via X-Tenant-ID."""
        # Test with superuser
        req_super = self.factory.get(
            "/api/v1/organizations/workspaces/",
            HTTP_X_TENANT_ID=str(self.tenant_a.id),
        )
        req_super.user = self.superuser

        middleware = self._get_middleware()
        resp_super = middleware(req_super)
        self.assertEqual(resp_super.status_code, 200)
        self.assertEqual(req_super.tenant, self.tenant_a)

        # Test with global tenant user (is_global=True)
        req_global = self.factory.get(
            "/api/v1/organizations/workspaces/",
            HTTP_X_TENANT_ID=str(self.tenant_b.id),
        )
        req_global.user = self.global_admin
        resp_global = middleware(req_global)
        self.assertEqual(resp_global.status_code, 200)
        self.assertEqual(req_global.tenant, self.tenant_b)

    def test_unauthenticated_request_without_header(self):
        """Unauthenticated request without header sets request.tenant to None."""
        request = self.factory.get("/api/v1/organizations/workspaces/")
        request.user = AnonymousUser()

        middleware = self._get_middleware()
        response = middleware(request)

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(request.tenant)

    def test_unauthenticated_request_with_header_yields_403(self):
        """Unauthenticated request with X-Tenant-ID header yields HTTP 403 on scoped endpoints."""
        request = self.factory.get(
            "/api/v1/organizations/workspaces/",
            HTTP_X_TENANT_ID=str(self.tenant_a.id),
        )
        request.user = AnonymousUser()

        middleware = self._get_middleware()
        response = middleware(request)

        self.assertEqual(response.status_code, 403)

    def test_non_tenant_scoped_endpoint_with_invalid_header_bypasses_tenant_check(self):
        """Non-tenant scoped endpoint (e.g., csrf, token, auth) ignores invalid X-Tenant-ID header."""
        request = self.factory.get(
            "/api/v1/csrf/",
            HTTP_X_TENANT_ID="nonexistent_or_invalid_id",
        )
        request.user = AnonymousUser()

        middleware = self._get_middleware()
        response = middleware(request)

        self.assertEqual(response.status_code, 200)

    def test_non_tenant_scoped_endpoint_with_unauthorized_header_bypasses_tenant_check(self):
        """Non-tenant scoped endpoint ignores unauthorized X-Tenant-ID header."""
        request = self.factory.post(
            "/api/v1/token/refresh/",
            HTTP_X_TENANT_ID=str(self.tenant_b.id),
        )
        request.user = self.user_a

        middleware = self._get_middleware()
        response = middleware(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(request.tenant, self.user_a.tenant)

    def test_tenant_creation_post_with_header_bypasses_tenant_check(self):
        """POST /api/v1/organizations/tenant/ creation bypasses X-Tenant-ID validation."""
        request = self.factory.post(
            "/api/v1/organizations/tenant/",
            HTTP_X_TENANT_ID="unrelated_tenant_id",
        )
        request.user = self.user_a

        middleware = self._get_middleware()
        response = middleware(request)

        self.assertEqual(response.status_code, 200)

    def test_subscription_endpoint_bypasses_tenant_header_check(self):
        """GET /api/v1/organizations/subscription/ bypasses X-Tenant-ID validation."""
        request = self.factory.get(
            "/api/v1/organizations/subscription/",
            HTTP_X_TENANT_ID="nonexistent_sub_tenant",
        )
        request.user = self.user_a

        middleware = self._get_middleware()
        response = middleware(request)

        self.assertEqual(response.status_code, 200)


class GlobalTenantHelperTests(TestCase):
    def test_get_global_tenant_retrieves_master(self):
        """get_global_tenant() retrieves the tenant marked is_global=True."""
        sub = Subscription.objects.create(name="Sub 1")
        tenant = Tenant.objects.create(name="Global Master", subscription=sub, is_global=True)

        found = get_global_tenant()
        self.assertIsNotNone(found)
        self.assertEqual(found.id, tenant.id)
        self.assertTrue(found.is_global)

    def test_get_global_tenant_returns_none_when_unconfigured(self):
        """get_global_tenant() returns None when no is_global=True tenant exists."""
        sub = Subscription.objects.create(name="Sub 2")
        Tenant.objects.create(name="Regular Tenant", subscription=sub, is_global=False)

        found = get_global_tenant()
        self.assertIsNone(found)


class TenantIsolationViewSetTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.subscription = Subscription.objects.create(name="Isolation Sub")
        self.global_tenant = Tenant.objects.create(
            name="Global Master Tenant", subscription=self.subscription, is_global=True
        )
        self.tenant_a = Tenant.objects.create(
            name="Tenant A", subscription=self.subscription, is_global=False
        )
        self.tenant_b = Tenant.objects.create(
            name="Tenant B", subscription=self.subscription, is_global=False
        )

        self.ws_a = Workspace.objects.create(name="WS A", tenant=self.tenant_a)
        self.ws_b = Workspace.objects.create(name="WS B", tenant=self.tenant_b)

        self.user_a = User.objects.create_user(
            username="user_iso_a", email="iso_a@test.com", tenant=self.tenant_a
        )
        self.user_b = User.objects.create_user(
            username="user_iso_b", email="iso_b@test.com", tenant=self.tenant_b
        )
        self.superuser = User.objects.create_superuser(
            username="super_iso", email="super_iso@test.com", tenant=self.global_tenant
        )

        from guardian.shortcuts import assign_perm
        assign_perm("view_workspace", self.user_a, self.ws_a)
        assign_perm("view_workspace", self.user_b, self.ws_b)
        assign_perm("view_tenant", self.user_a, self.tenant_a)
        assign_perm("view_tenant", self.user_b, self.tenant_b)
        assign_perm("view_user", self.user_a, self.user_a)
        assign_perm("view_user", self.user_b, self.user_b)

        admin_role_a = get_or_create_admin_role(self.ws_a)
        WorkspaceMembership.objects.create(
            workspace=self.ws_a, user=self.user_a, role=admin_role_a
        )
        admin_role_b = get_or_create_admin_role(self.ws_b)
        WorkspaceMembership.objects.create(
            workspace=self.ws_b, user=self.user_b, role=admin_role_b
        )

    def test_database_unique_constraint_rejects_second_global_tenant(self):
        """Database partial unique constraint rejects creating a second is_global=True tenant."""
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Tenant.objects.create(
                name="Second Global Tenant",
                subscription=self.subscription,
                is_global=True,
            )

    def test_workspace_queryset_scoped_to_active_tenant_for_non_global_user(self):
        """Non-global user cannot see workspaces belonging to other tenants."""
        from organizations.views import WorkspaceViewSet
        view = WorkspaceViewSet()
        request = self.factory.get("/api/v1/organizations/workspaces/")
        request.user = self.user_a
        request.tenant = self.tenant_a
        view.request = request

        qs = view.get_queryset()
        self.assertIn(self.ws_a, qs)
        self.assertNotIn(self.ws_b, qs)

    def test_workspace_queryset_scoped_by_header_for_superuser(self):
        """Superuser with X-Tenant-ID header only sees workspaces for the scoped tenant."""
        from organizations.views import WorkspaceViewSet
        view = WorkspaceViewSet()
        request = self.factory.get(
            "/api/v1/organizations/workspaces/",
            HTTP_X_TENANT_ID=str(self.tenant_a.id),
        )
        request.user = self.superuser
        request.tenant = self.tenant_a
        view.request = request

        qs = view.get_queryset()
        self.assertIn(self.ws_a, qs)
        self.assertNotIn(self.ws_b, qs)

    def test_tenant_queryset_scoped_to_active_tenant(self):
        """TenantViewSet.get_queryset isolates non-global users to their active tenant."""
        from organizations.views import TenantViewSet
        view = TenantViewSet()
        request = self.factory.get("/api/v1/organizations/tenants/")
        request.user = self.user_a
        request.tenant = self.tenant_a
        view.request = request

        qs = view.get_queryset()
        self.assertIn(self.tenant_a, qs)
        self.assertNotIn(self.tenant_b, qs)
        self.assertNotIn(self.global_tenant, qs)

    def test_workspace_creation_cross_tenant_rejected_for_non_global_user(self):
        """Creating a workspace for a different tenant than request.tenant is rejected."""
        from organizations.views import WorkspaceViewSet
        from organizations.serializers import WorkspaceSerializer
        view = WorkspaceViewSet()
        request = self.factory.post("/api/v1/organizations/workspaces/")
        request.user = self.user_a
        request.tenant = self.tenant_a
        view.request = request

        serializer = WorkspaceSerializer(
            data={"name": "Malicious WS", "description": "Desc", "tenant": self.tenant_b.id}
        )
        serializer.is_valid(raise_exception=True)

        with self.assertRaises(PermissionError):
            view.perform_create(serializer)

    def test_subscription_list_allowed_for_tenantless_user(self):
        """Authenticated tenantless user can list subscriptions without tenant context."""
        tenantless_user = User.objects.create_user(
            username="tenantless_sub_tester",
            email="tenantless_sub@test.com",
            tenant=None,
        )
        client = APIClient()
        client.force_authenticate(user=tenantless_user)

        response = client.get("/api/v1/organizations/subscription/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Subscriptions should be listed
        self.assertGreaterEqual(len(response.data), 1)

    def test_cors_preflight_allows_custom_tenant_and_workspace_headers(self):
        """CORS preflight (OPTIONS) returns Access-Control-Allow-Headers containing x-tenant-id and x-workspace-id."""
        client = APIClient()
        origin = "http://localhost:5173"
        response = client.options(
            "/api/v1/organizations/tenant/",
            HTTP_ORIGIN=origin,
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="GET",
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS="authorization,x-tenant-id,x-workspace-id,x-client-platform",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        allow_headers = response.headers.get("Access-Control-Allow-Headers", "").lower()
        self.assertIn("x-tenant-id", allow_headers)
        self.assertIn("x-workspace-id", allow_headers)
        self.assertIn("x-client-platform", allow_headers)

    def test_tenant_member_can_list_workspaces_via_api(self):
        """Authenticated tenant member can list workspaces within their tenant context via API."""
        client = APIClient()
        client.force_authenticate(user=self.user_a)
        response = client.get(
            "/api/v1/organizations/workspace/",
            HTTP_X_TENANT_ID=str(self.tenant_a.id),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        workspace_ids = [w["id"] for w in response.data]
        self.assertIn(self.ws_a.id, workspace_ids)
        self.assertNotIn(self.ws_b.id, workspace_ids)

    def test_tenant_member_can_list_tenants_via_api(self):
        """Authenticated tenant member can list their active tenant via API."""
        client = APIClient()
        client.force_authenticate(user=self.user_a)
        response = client.get(
            "/api/v1/organizations/tenant/",
            HTTP_X_TENANT_ID=str(self.tenant_a.id),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        tenant_ids = [t["id"] for t in response.data]
        self.assertIn(self.tenant_a.id, tenant_ids)
        self.assertNotIn(self.tenant_b.id, tenant_ids)

    def test_cross_tenant_workspace_listing_denied(self):
        """User affiliated with Tenant A attempting to list workspaces with Tenant B's X-Tenant-ID is rejected."""
        client = APIClient()
        client.force_authenticate(user=self.user_a)
        response = client.get(
            "/api/v1/organizations/workspace/",
            HTTP_X_TENANT_ID=str(self.tenant_b.id),
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_tenant_member_can_create_workspace_via_api(self):
        """Tenant owner can create a workspace for their tenant via API."""
        client = APIClient()
        client.force_authenticate(user=self.user_a)
        response = client.post(
            "/api/v1/organizations/workspace/",
            {"name": "New Alpha Workspace", "description": "Created by owner", "tenant": self.tenant_a.id},
            format="json",
            HTTP_X_TENANT_ID=str(self.tenant_a.id),
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "New Alpha Workspace")

    def test_tenant_member_can_list_users_via_api(self):
        """Authenticated tenant member can list viewable users within their tenant context via API."""
        client = APIClient()
        client.force_authenticate(user=self.user_a)
        response = client.get(
            "/api/v1/users/user/",
            HTTP_X_TENANT_ID=str(self.tenant_a.id),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user_ids = [u["id"] for u in response.data]
        self.assertIn(self.user_a.id, user_ids)
        self.assertNotIn(self.user_b.id, user_ids)

    def test_tenant_member_can_list_users_with_workspace_param_via_api(self):
        """Authenticated tenant member can list users filtered by workspace parameter via API."""
        client = APIClient()
        client.force_authenticate(user=self.user_a)
        response = client.get(
            f"/api/v1/users/user/?workspace={self.ws_a.id}",
            HTTP_X_TENANT_ID=str(self.tenant_a.id),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_cross_tenant_user_listing_denied(self):
        """User affiliated with Tenant A attempting to list users with Tenant B's X-Tenant-ID is rejected."""
        client = APIClient()
        client.force_authenticate(user=self.user_a)
        response = client.get(
            "/api/v1/users/user/",
            HTTP_X_TENANT_ID=str(self.tenant_b.id),
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

