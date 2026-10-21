from django.test import TestCase
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth.models import Group
from guardian.shortcuts import assign_perm

from organizations.models import Tenant, Workspace, Subscription
from organizations.helpers import get_or_create_admin_role, get_no_role
from roles.models import Role, WorkspaceMembership
from users.models import User
from support.models import (
    Ticket,
    Comment,
    Attachment,
    CommentAttachment,
    SupportMembership,
)
from support.serializers import TicketSerializer


class SupportMultitenancyTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.subscription = Subscription.objects.create(name="Sub", description="Sub")

        self.master_tenant = Tenant.objects.create(
            name="Master Tenant",
            subscription=self.subscription,
            is_global=True,
        )
        self.tenant_alpha = Tenant.objects.create(
            name="Tenant Alpha",
            subscription=self.subscription,
            is_global=False,
        )
        self.tenant_beta = Tenant.objects.create(
            name="Tenant Beta",
            subscription=self.subscription,
            is_global=False,
        )

        self.ws_alpha = Workspace.objects.create(
            name="WS Alpha", tenant=self.tenant_alpha
        )
        self.ws_beta = Workspace.objects.create(
            name="WS Beta", tenant=self.tenant_beta
        )

        # Global Support Manager
        self.support_manager = User.objects.create_user(
            username="support_mgr",
            email="mgr@test.com",
            tenant=self.master_tenant,
        )
        self.support_membership = SupportMembership.objects.create(
            user=self.support_manager,
            role="support_manager",
            tenant=self.master_tenant,
        )

        # Tenant Alpha Admin User
        self.alpha_admin = User.objects.create_user(
            username="alpha_admin",
            email="alpha_admin@test.com",
            tenant=self.tenant_alpha,
        )
        self.admin_role_alpha = get_or_create_admin_role(self.ws_alpha)
        WorkspaceMembership.objects.create(
            user=self.alpha_admin,
            workspace=self.ws_alpha,
            role=self.admin_role_alpha,
        )

        # Tenant Alpha Regular User
        self.alpha_user = User.objects.create_user(
            username="alpha_user",
            email="alpha_user@test.com",
            tenant=self.tenant_alpha,
        )
        self.no_role_alpha = get_no_role(self.ws_alpha)
        WorkspaceMembership.objects.create(
            user=self.alpha_user,
            workspace=self.ws_alpha,
            role=self.no_role_alpha,
        )

        # Tenant Beta Regular User
        self.beta_user = User.objects.create_user(
            username="beta_user",
            email="beta_user@test.com",
            tenant=self.tenant_beta,
        )
        self.no_role_beta = get_no_role(self.ws_beta)
        WorkspaceMembership.objects.create(
            user=self.beta_user,
            workspace=self.ws_beta,
            role=self.no_role_beta,
        )

        # Tickets
        self.ticket_alpha = Ticket.objects.create(
            title="Alpha Ticket",
            description="Alpha issue",
            tenant=self.tenant_alpha,
            workspace=self.ws_alpha,
            user=self.alpha_user,
            assigned_to=self.support_manager,
        )
        self.ticket_beta = Ticket.objects.create(
            title="Beta Ticket",
            description="Beta issue",
            tenant=self.tenant_beta,
            workspace=self.ws_beta,
            user=self.beta_user,
            assigned_to=self.support_manager,
        )

    def test_ticket_clean_rejects_cross_tenant_workspace(self):
        """Ticket model clean() rejects ticket if workspace does not belong to ticket tenant."""
        ticket = Ticket(
            title="Invalid Ticket",
            description="Invalid WS",
            tenant=self.tenant_alpha,
            workspace=self.ws_beta,  # Belongs to Beta
            user=self.alpha_user,
        )
        with self.assertRaises(ValidationError):
            ticket.clean()

    def test_ticket_serializer_rejects_cross_tenant_workspace(self):
        """TicketSerializer validation fails if workspace tenant does not match ticket tenant."""
        serializer = TicketSerializer(
            data={
                "title": "Serializer Invalid",
                "description": "Invalid WS",
                "tenant": self.tenant_alpha.id,
                "workspace": self.ws_beta.id,
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("workspace", serializer.errors)

    def test_guest_ticket_creation_associates_resolved_tenant(self):
        """Unauthenticated guest can submit a ticket with target tenant ID and guest contact."""
        payload = {
            "title": "Guest Ticket",
            "description": "Guest cannot log in",
            "guest_name": "John Doe",
            "guest_email": "guest@external.com",
            "tenant": str(self.tenant_alpha.id),
        }
        response = self.client.post("/api/v1/support/tickets/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created = Ticket.objects.get(id=response.data["id"])
        self.assertIsNone(created.user)
        self.assertEqual(created.tenant, self.tenant_alpha)
        self.assertEqual(created.assigned_to, self.support_manager)

    def test_support_membership_tenant_association(self):
        """SupportMembership records associate with tenant or remain global if tenant is null or master."""
        local_membership = SupportMembership.objects.create(
            user=self.alpha_user,
            role="support_agent",
            tenant=self.tenant_alpha,
        )
        self.assertEqual(local_membership.tenant, self.tenant_alpha)

        global_membership = SupportMembership.objects.create(
            user=self.support_manager,
            role="support_manager",
            tenant=None,
        )
        self.assertIsNone(global_membership.tenant)

    def test_ticket_queryset_scoping_tenant_isolation(self):
        """Regular user in Tenant Alpha only sees Tenant Alpha tickets, never Tenant Beta."""
        self.client.force_authenticate(user=self.alpha_user)
        response = self.client.get(
            "/api/v1/support/tickets/",
            HTTP_X_TENANT_ID=str(self.tenant_alpha.id),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ticket_ids = [t["id"] for t in response.data]
        self.assertIn(str(self.ticket_alpha.id), ticket_ids)
        self.assertNotIn(str(self.ticket_beta.id), ticket_ids)

    def test_cross_tenant_ticket_retrieval_denied_for_unauthorized_user(self):
        """User in Tenant Alpha is denied retrieving a ticket belonging to Tenant Beta."""
        self.client.force_authenticate(user=self.alpha_user)
        response = self.client.get(
            f"/api/v1/support/tickets/{self.ticket_beta.id}/",
            HTTP_X_TENANT_ID=str(self.tenant_alpha.id),
        )
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_cross_tenant_ticket_update_denied_for_unauthorized_user(self):
        """User in Tenant Alpha is denied updating a ticket belonging to Tenant Beta."""
        self.client.force_authenticate(user=self.alpha_user)
        response = self.client.patch(
            f"/api/v1/support/tickets/{self.ticket_beta.id}/",
            {"priority": "high"},
            format="json",
            HTTP_X_TENANT_ID=str(self.tenant_alpha.id),
        )
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_comment_creation_rejected_on_unassigned_cross_tenant_ticket(self):
        """User in Tenant Alpha cannot create a comment on Tenant Beta ticket."""
        self.client.force_authenticate(user=self.alpha_user)
        response = self.client.post(
            "/api/v1/support/comments/",
            {
                "ticket": str(self.ticket_beta.id),
                "content": "Cross tenant comment attempt",
            },
            format="json",
            HTTP_X_TENANT_ID=str(self.tenant_alpha.id),
        )
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])
        self.assertFalse(Comment.objects.filter(content="Cross tenant comment attempt").exists())

    def test_comment_listing_scoped_to_active_tenant(self):
        """Comments are strictly filtered by active tenant; Beta comments are never returned to Alpha user."""
        comment_alpha = Comment.objects.create(
            ticket=self.ticket_alpha,
            user=self.alpha_user,
            content="Alpha comment",
        )
        comment_beta = Comment.objects.create(
            ticket=self.ticket_beta,
            user=self.beta_user,
            content="Beta comment",
        )

        self.client.force_authenticate(user=self.alpha_user)
        response = self.client.get(
            "/api/v1/support/comments/",
            HTTP_X_TENANT_ID=str(self.tenant_alpha.id),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        comment_ids = [c["id"] for c in response.data]
        self.assertIn(comment_alpha.id, comment_ids)
        self.assertNotIn(comment_beta.id, comment_ids)

    def test_global_support_manager_cross_tenant_access(self):
        """Global support manager can view and manage tickets across customer tenants."""
        self.client.force_authenticate(user=self.support_manager)
        response = self.client.get("/api/v1/support/tickets/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ticket_ids = [t["id"] for t in response.data]
        self.assertIn(str(self.ticket_alpha.id), ticket_ids)
        self.assertIn(str(self.ticket_beta.id), ticket_ids)

        # Can retrieve individual tickets across tenants
        resp_alpha = self.client.get(f"/api/v1/support/tickets/{self.ticket_alpha.id}/")
        self.assertEqual(resp_alpha.status_code, status.HTTP_200_OK)
        resp_beta = self.client.get(f"/api/v1/support/tickets/{self.ticket_beta.id}/")
        self.assertEqual(resp_beta.status_code, status.HTTP_200_OK)

    def test_tenant_user_lacking_change_perm_denied_patch(self):
        """Regular tenant user lacking change_ticket permission cannot update ticket."""
        self.client.force_authenticate(user=self.alpha_user)
        response = self.client.patch(
            f"/api/v1/support/tickets/{self.ticket_alpha.id}/",
            {"priority": "high"},
            format="json",
            HTTP_X_TENANT_ID=str(self.tenant_alpha.id),
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
