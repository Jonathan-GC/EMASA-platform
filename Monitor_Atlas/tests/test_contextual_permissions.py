from django.test import TestCase, override_settings
from django.contrib.auth.models import Group
from django.conf import settings
from rest_framework.test import APIClient
from rest_framework import status
from guardian.shortcuts import assign_perm
from auditlog.models import LogEntry

from organizations.models import Tenant, Workspace, Subscription
from roles.models import Role, WorkspaceMembership
from roles.permissions import has_contextual_perm, HasContextualPermission
from users.models import User
from infrastructure.models import Machine


class ContextualPermissionEvaluatorTests(TestCase):
    def setUp(self):
        self.subscription = Subscription.objects.create(name="Sub", description="Sub")
        self.global_tenant = Tenant.objects.create(
            name="Global Master Tenant",
            subscription=self.subscription,
            is_global=True,
        )
        self.tenant_1 = Tenant.objects.create(
            name="Tenant 1",
            subscription=self.subscription,
            is_global=False,
        )
        self.tenant_2 = Tenant.objects.create(
            name="Tenant 2",
            subscription=self.subscription,
            is_global=False,
        )

        # Workspaces
        self.ws_alpha = Workspace.objects.create(name="WS Alpha", tenant=self.tenant_1)
        self.ws_beta = Workspace.objects.create(name="WS Beta", tenant=self.tenant_1)
        self.ws_gamma = Workspace.objects.create(name="WS Gamma", tenant=self.tenant_2)

        # Groups & Roles in WS Alpha
        self.role_group_alpha = Group.objects.create(name="group_alpha")
        self.role_alpha = Role.objects.create(
            name="Role Alpha", workspace=self.ws_alpha, group=self.role_group_alpha
        )
        assign_perm("infrastructure.delete_machine", self.role_group_alpha)
        assign_perm("infrastructure.view_machine", self.role_group_alpha)

        # Groups & Roles in WS Beta
        self.role_group_beta = Group.objects.create(name="group_beta")
        self.role_beta = Role.objects.create(
            name="Role Beta", workspace=self.ws_beta, group=self.role_group_beta
        )
        assign_perm("infrastructure.view_machine", self.role_group_beta)

        # Test User
        self.user = User.objects.create_user(
            username="multi_role_user", email="multi@test.com", tenant=self.tenant_1
        )
        # Assign user to Alpha with Role Alpha
        WorkspaceMembership.objects.create(
            user=self.user, workspace=self.ws_alpha, role=self.role_alpha
        )
        self.user.groups.add(self.role_group_alpha)

        # Assign user to Beta with Role Beta
        WorkspaceMembership.objects.create(
            user=self.user, workspace=self.ws_beta, role=self.role_beta
        )
        self.user.groups.add(self.role_group_beta)

        # Superuser
        self.superuser = User.objects.create_superuser(
            username="super_eval", email="super_eval@test.com", tenant=self.global_tenant
        )

        # Global Admin
        self.global_admin_group, _ = Group.objects.get_or_create(name="global_admin")
        self.global_admin = User.objects.create_user(
            username="global_admin_eval", email="gadmin@test.com", tenant=self.global_tenant
        )
        self.global_admin.groups.add(self.global_admin_group)

    def test_positive_permission_evaluation(self):
        """User with active role in workspace is granted permission."""
        has_perm = has_contextual_perm(
            self.user, "view_machine", workspace=self.ws_alpha
        )
        self.assertTrue(has_perm)

        has_delete_alpha = has_contextual_perm(
            self.user, "delete_machine", workspace=self.ws_alpha
        )
        self.assertTrue(has_delete_alpha)

    def test_cross_workspace_permission_isolation(self):
        """User with delete_machine in Alpha is denied delete_machine in Beta (no cross-workspace leakage)."""
        # User has view_machine in Beta
        self.assertTrue(has_contextual_perm(self.user, "view_machine", workspace=self.ws_beta))

        # But must NOT have delete_machine in Beta, even though user is in group_alpha in Django's flat user.groups
        has_delete_beta = has_contextual_perm(
            self.user, "delete_machine", workspace=self.ws_beta
        )
        self.assertFalse(has_delete_beta)

    def test_cross_tenant_permission_isolation_zero_leakage(self):
        """User in Tenant 1 has zero permissions in Tenant 2 workspaces."""
        # User has no membership in WS Gamma (Tenant 2)
        has_view_gamma = has_contextual_perm(
            self.user, "view_machine", workspace=self.ws_gamma
        )
        self.assertFalse(has_view_gamma)

        has_tenant_2 = has_contextual_perm(
            self.user, "change_tenant", tenant=self.tenant_2
        )
        self.assertFalse(has_tenant_2)

    def test_superuser_contextual_bypass(self):
        """Superuser always evaluates to True across any workspace or tenant."""
        self.assertTrue(
            has_contextual_perm(self.superuser, "delete_machine", workspace=self.ws_alpha)
        )
        self.assertTrue(
            has_contextual_perm(self.superuser, "delete_machine", workspace=self.ws_gamma)
        )

    def test_global_administrator_bypass_with_audit_logging(self):
        """Global administrator from global master tenant bypasses checks and records audit log."""
        initial_log_count = LogEntry.objects.count()
        has_perm = has_contextual_perm(
            self.global_admin,
            "delete_machine",
            tenant=self.tenant_1,
            workspace=self.ws_alpha,
        )
        self.assertTrue(has_perm)
        self.assertGreater(LogEntry.objects.count(), initial_log_count)


class ContextualDRFPermissionTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.subscription = Subscription.objects.create(name="Sub DRF", description="Sub")
        self.tenant_1 = Tenant.objects.create(
            name="DRF Tenant 1", subscription=self.subscription, is_global=False
        )
        self.tenant_2 = Tenant.objects.create(
            name="DRF Tenant 2", subscription=self.subscription, is_global=False
        )

        self.ws_1 = Workspace.objects.create(name="WS 1", tenant=self.tenant_1)
        self.ws_2 = Workspace.objects.create(name="WS 2", tenant=self.tenant_1)
        self.ws_t2 = Workspace.objects.create(name="WS T2", tenant=self.tenant_2)

        # Role & User in WS 1
        self.group_1 = Group.objects.create(name="g1")
        self.role_1 = Role.objects.create(
            name="Manager", workspace=self.ws_1, group=self.group_1, is_admin=True
        )
        assign_perm("roles.view_role", self.group_1)
        assign_perm("roles.change_role", self.group_1)
        assign_perm("change_workspace", self.group_1, self.ws_1)

        self.user = User.objects.create_user(
            username="drf_user", email="drf@test.com", tenant=self.tenant_1
        )
        WorkspaceMembership.objects.create(
            user=self.user, workspace=self.ws_1, role=self.role_1
        )
        assign_perm("change_workspace", self.user, self.ws_1)

        # Role belonging to WS 2 (same tenant, different workspace)
        self.role_ws_2 = Role.objects.create(name="Other WS Role", workspace=self.ws_2)

        # Role belonging to Tenant 2
        self.role_tenant_2 = Role.objects.create(name="T2 Role", workspace=self.ws_t2)

    def test_viewset_authorized_request_with_context(self):
        """Request with active workspace context and valid permission succeeds."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            f"/api/v1/roles/role/?workspace={self.ws_1.id}",
            HTTP_X_TENANT_ID=str(self.tenant_1.id),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_viewset_denied_when_missing_workspace_context_on_scoped_list(self):
        """List request on workspace-scoped viewset without workspace context returns 403."""
        self.client.force_authenticate(user=self.user)
        # Omit workspace parameter and header
        response = self.client.get(
            "/api/v1/roles/role/",
            HTTP_X_TENANT_ID=str(self.tenant_1.id),
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_viewset_denied_when_lacking_permission(self):
        """Request requiring ungranted permission (e.g. add_role) is denied with 403."""
        self.client.force_authenticate(user=self.user)
        # user lacks add_role
        response = self.client.post(
            f"/api/v1/roles/role/?workspace={self.ws_1.id}",
            {"name": "New Role", "workspace": str(self.ws_1.id)},
            format="json",
            HTTP_X_TENANT_ID=str(self.tenant_1.id),
            HTTP_X_WORKSPACE_ID=str(self.ws_1.id),
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_object_level_workspace_boundary_rejection(self):
        """Accessing an object in Workspace 2 with context set to Workspace 1 returns 403 or 404."""
        self.client.force_authenticate(user=self.user)
        # Request object from ws_2 with header set to ws_1
        response = self.client.get(
            f"/api/v1/roles/role/{self.role_ws_2.id}/",
            HTTP_X_TENANT_ID=str(self.tenant_1.id),
            HTTP_X_WORKSPACE_ID=str(self.ws_1.id),
        )
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_object_level_tenant_boundary_rejection(self):
        """Accessing an object belonging to Tenant 2 while scoped to Tenant 1 returns 403 or 404."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            f"/api/v1/roles/role/{self.role_tenant_2.id}/",
            HTTP_X_TENANT_ID=str(self.tenant_1.id),
            HTTP_X_WORKSPACE_ID=str(self.ws_1.id),
        )
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_has_object_permission_boundary_mismatch_direct(self):
        """Direct invocation of has_object_permission with mismatched context raises PermissionDenied (403)."""
        from rest_framework.request import Request
        from django.test import RequestFactory
        from rest_framework.exceptions import PermissionDenied
        from roles.views import RoleViewSet

        factory = RequestFactory()
        req = factory.get(f"/api/v1/roles/role/{self.role_ws_2.id}/")
        drf_req = Request(req)
        drf_req.user = self.user
        drf_req.tenant = self.tenant_1
        drf_req.workspace = self.ws_1

        view = RoleViewSet()
        view.action = "retrieve"
        view.scope = "role"

        checker = HasContextualPermission()
        with self.assertRaises(PermissionDenied):
            checker.has_object_permission(drf_req, view, self.role_ws_2)

    @override_settings(SERVICE_API_KEY="valid-service-secret-key-999")
    def test_service_api_key_bypass(self):
        """Requests with valid X-Service-API-Key or X-API-Key bypass user contextual checks."""
        # Unauthenticated request with X-Service-API-Key header
        response = self.client.get(
            f"/api/v1/roles/role/?workspace={self.ws_1.id}",
            HTTP_X_SERVICE_API_KEY="valid-service-secret-key-999",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Also supports X-API-Key header
        response_alt = self.client.get(
            f"/api/v1/roles/role/?workspace={self.ws_1.id}",
            HTTP_X_API_KEY="valid-service-secret-key-999",
        )
        self.assertEqual(response_alt.status_code, status.HTTP_200_OK)
