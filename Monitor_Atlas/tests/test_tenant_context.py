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
        """Unauthenticated request with X-Tenant-ID header yields HTTP 403."""
        request = self.factory.get(
            "/api/v1/organizations/workspaces/",
            HTTP_X_TENANT_ID=str(self.tenant_a.id),
        )
        request.user = AnonymousUser()

        middleware = self._get_middleware()
        response = middleware(request)

        self.assertEqual(response.status_code, 403)


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

