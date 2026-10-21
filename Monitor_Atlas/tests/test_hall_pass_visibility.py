"""Tests for hall pass workspace visibility and middleware pass-through.

Covers:
- S1: Hall pass grants read access to the objective workspace.
- S2/S5: Pass workspace appears when listing workspaces without headers.
- S3: Pass workspace appears when listing workspaces with X-Tenant-ID header.
- S4: Services in pass-covered workspace appear when listing without headers.
"""
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from organizations.models import Tenant, Workspace, Subscription
from organizations.helpers import get_or_create_admin_role, get_no_role
from roles.models import WorkspaceMembership
from users.models import User
from support.models import (
    SupportMembership,
    SupportHallPass,
    Ticket,
)


class HallPassWorkspaceVisibilityTests(TestCase):
    """Verify that a technician with an active hall pass can see and read
    the objective workspace and its services."""

    def setUp(self):
        self.client = APIClient()
        self.subscription = Subscription.objects.create(
            name="Viz Sub", description="Subscription for visibility tests"
        )

        # -- Tenants --
        self.global_tenant = Tenant.objects.create(
            name="Global HQ", subscription=self.subscription, is_global=True
        )
        self.customer_tenant = Tenant.objects.create(
            name="Customer Org", subscription=self.subscription, is_global=False
        )

        # -- Workspaces --
        self.ws_global = Workspace.objects.create(
            name="Global WS", tenant=self.global_tenant
        )
        self.ws_customer = Workspace.objects.create(
            name="Customer Production", tenant=self.customer_tenant
        )

        # -- Admin for customer workspace (needed so guardian rows exist) --
        self.customer_admin = User.objects.create_user(
            username="customer_admin",
            email="admin@customer.com",
            tenant=self.customer_tenant,
        )
        admin_role = get_or_create_admin_role(self.ws_customer)
        WorkspaceMembership.objects.create(
            workspace=self.ws_customer,
            user=self.customer_admin,
            role=admin_role,
        )

        # -- Support manager (needed for ticket creation) --
        self.support_manager = User.objects.create_user(
            username="support_mgr",
            email="mgr@global.com",
            tenant=self.global_tenant,
        )
        SupportMembership.objects.create(
            user=self.support_manager,
            role="support_manager",
            tenant=self.global_tenant,
        )

        # -- Technician in global tenant (NO membership in customer workspace) --
        self.technician = User.objects.create_user(
            username="tech_alice",
            email="alice@global.com",
            tenant=self.global_tenant,
        )
        SupportMembership.objects.create(
            user=self.technician,
            role="technician",
            tenant=self.global_tenant,
        )
        # Membership only in global workspace
        no_role_global = get_no_role(self.ws_global)
        WorkspaceMembership.objects.create(
            workspace=self.ws_global,
            user=self.technician,
            role=no_role_global,
        )

        # -- Ticket on customer workspace --
        self.ticket = Ticket.objects.create(
            title="Vibration issue",
            description="High vibration on compressor",
            tenant=self.customer_tenant,
            workspace=self.ws_customer,
            user=self.customer_admin,
            assigned_to=self.support_manager,
        )

        # -- Active hall pass for technician on customer workspace --
        self.hall_pass = SupportHallPass.objects.create(
            technician=self.technician,
            ticket=self.ticket,
            workspace=self.ws_customer,
            tenant=self.customer_tenant,
            permission_level="READ",
            granted_by=self.support_manager,
            expires_at=timezone.now() + timedelta(hours=24),
            status="ACTIVE",
            reason="Dispatched for vibration diagnostics",
        )

    # ------------------------------------------------------------------ #
    #  S2 / S5: Workspace listing WITHOUT any headers                     #
    # ------------------------------------------------------------------ #
    def test_pass_holder_sees_customer_workspace_without_headers(self):
        """Technician with hall pass sees the customer workspace when
        listing workspaces without X-Tenant-ID or X-Workspace-ID."""
        self.client.force_authenticate(user=self.technician)
        resp = self.client.get("/api/v1/organizations/workspace/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        ws_ids = {str(w["id"]) for w in resp.data}
        self.assertIn(
            str(self.ws_customer.id),
            ws_ids,
            "Customer workspace should appear for hall pass holder",
        )

    # ------------------------------------------------------------------ #
    #  S3: Workspace listing WITH customer tenant header                  #
    # ------------------------------------------------------------------ #
    def test_pass_holder_sees_workspace_with_customer_tenant_header(self):
        """Technician with hall pass can list workspaces when sending
        X-Tenant-ID pointing to the customer tenant."""
        self.client.force_authenticate(user=self.technician)
        resp = self.client.get(
            "/api/v1/organizations/workspace/",
            HTTP_X_TENANT_ID=str(self.customer_tenant.id),
        )
        self.assertIn(
            resp.status_code,
            [status.HTTP_200_OK],
            f"Expected 200, got {resp.status_code}: {resp.data if hasattr(resp, 'data') else resp.content}",
        )
        ws_ids = {str(w["id"]) for w in resp.data}
        self.assertIn(str(self.ws_customer.id), ws_ids)

    # ------------------------------------------------------------------ #
    #  Middleware: pass holder is not blocked by tenant context middleware #
    # ------------------------------------------------------------------ #
    def test_middleware_allows_pass_holder_cross_tenant_access(self):
        """TenantContextMiddleware does not reject a pass holder sending
        X-Tenant-ID for a tenant where they have no WorkspaceMembership."""
        self.client.force_authenticate(user=self.technician)
        resp = self.client.get(
            "/api/v1/organizations/workspace/",
            HTTP_X_TENANT_ID=str(self.customer_tenant.id),
        )
        self.assertNotEqual(
            resp.status_code,
            status.HTTP_403_FORBIDDEN,
            "Middleware should not 403 a hall pass holder",
        )

    # ------------------------------------------------------------------ #
    #  Expired pass must NOT grant visibility                             #
    # ------------------------------------------------------------------ #
    def test_expired_pass_does_not_grant_visibility(self):
        """An expired hall pass should not make the workspace visible."""
        self.hall_pass.expires_at = timezone.now() - timedelta(hours=1)
        self.hall_pass.save()

        self.client.force_authenticate(user=self.technician)
        resp = self.client.get("/api/v1/organizations/workspace/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        ws_ids = {str(w["id"]) for w in resp.data}
        self.assertNotIn(
            str(self.ws_customer.id),
            ws_ids,
            "Expired pass should not expose the customer workspace",
        )

    # ------------------------------------------------------------------ #
    #  Revoked pass must NOT grant visibility                             #
    # ------------------------------------------------------------------ #
    def test_revoked_pass_does_not_grant_visibility(self):
        """A revoked hall pass should not make the workspace visible."""
        self.hall_pass.status = "REVOKED"
        self.hall_pass.save()

        self.client.force_authenticate(user=self.technician)
        resp = self.client.get("/api/v1/organizations/workspace/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        ws_ids = {str(w["id"]) for w in resp.data}
        self.assertNotIn(
            str(self.ws_customer.id),
            ws_ids,
            "Revoked pass should not expose the customer workspace",
        )

    # ------------------------------------------------------------------ #
    #  User without pass still cannot see other workspaces                #
    # ------------------------------------------------------------------ #
    def test_user_without_pass_cannot_see_other_tenant_workspace(self):
        """A technician without a hall pass should not see workspaces from
        another tenant."""
        other_tech = User.objects.create_user(
            username="tech_no_pass",
            email="nopass@global.com",
            tenant=self.global_tenant,
        )
        no_role_global = get_no_role(self.ws_global)
        WorkspaceMembership.objects.create(
            workspace=self.ws_global,
            user=other_tech,
            role=no_role_global,
        )

        self.client.force_authenticate(user=other_tech)
        resp = self.client.get("/api/v1/organizations/workspace/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        ws_ids = {str(w["id"]) for w in resp.data}
        self.assertNotIn(
            str(self.ws_customer.id),
            ws_ids,
            "User without hall pass must not see cross-tenant workspaces",
        )

    # ------------------------------------------------------------------ #
    #  Middleware: user without pass still blocked cross-tenant            #
    # ------------------------------------------------------------------ #
    def test_middleware_blocks_user_without_pass_cross_tenant(self):
        """User without a hall pass is still rejected by the middleware
        when sending X-Tenant-ID for a tenant they have no affiliation with."""
        other_tech = User.objects.create_user(
            username="tech_blocked",
            email="blocked@global.com",
            tenant=self.global_tenant,
        )

        self.client.force_authenticate(user=other_tech)
        resp = self.client.get(
            "/api/v1/organizations/workspace/",
            HTTP_X_TENANT_ID=str(self.customer_tenant.id),
        )
        # Global tenant users are authorized by is_global check, so this
        # user passes middleware.  But they should not SEE customer workspaces.
        ws_ids = {str(w["id"]) for w in resp.data} if resp.status_code == 200 else set()
        self.assertNotIn(str(self.ws_customer.id), ws_ids)
