from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient
from rest_framework import status
from auditlog.models import LogEntry

from organizations.models import Tenant, Workspace, Subscription
from roles.models import Role, WorkspaceMembership
from users.models import User
from chirpstack.models import DeviceProfile
from infrastructure.models import Machine, Device, Application, Type
from support.models import (
    Ticket,
    Comment,
    SupportMembership,
    TechnicianAssignment,
)


class TechnicianDispatchTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.subscription = Subscription.objects.create(name="Sub", description="Sub")

        # Tenants
        self.master_tenant = Tenant.objects.create(
            name="Master Central Tenant",
            subscription=self.subscription,
            is_global=True,
        )
        self.tenant_alpha = Tenant.objects.create(
            name="Customer Alpha Tenant",
            subscription=self.subscription,
            is_global=False,
        )

        # Workspaces
        self.ws_master = Workspace.objects.create(
            name="Master WS", tenant=self.master_tenant
        )
        self.ws_alpha = Workspace.objects.create(
            name="Alpha Production WS", tenant=self.tenant_alpha
        )

        # Infrastructure in Alpha
        self.machine_alpha = Machine.objects.create(
            name="Alpha Compressor", workspace=self.ws_alpha
        )
        self.app_alpha = Application.objects.create(
            name="Alpha Application", workspace=self.ws_alpha
        )
        self.dp_alpha = DeviceProfile.objects.create(
            name="Alpha Profile",
            workspace=self.ws_alpha,
            region="US915",
            abp_rx1_delay=1,
            abp_rx1_dr_offset=0,
            abp_rx2_dr=0,
            abp_rx2_freq=923300000,
        )
        self.device_type = Type.objects.create(name="Vibration Sensor Type")
        self.device_alpha = Device.objects.create(
            dev_eui="AABBCCDDEEFF0011",
            name="Vibration Sensor 1",
            description="Alpha Sensor",
            workspace=self.ws_alpha,
            machine=self.machine_alpha,
            application=self.app_alpha,
            device_profile=self.dp_alpha,
            device_type=self.device_type,
        )

        # Global Support Manager in Master Tenant
        self.support_manager = User.objects.create_user(
            username="manager_bob",
            email="manager@master.com",
            tenant=self.master_tenant,
        )
        SupportMembership.objects.create(
            user=self.support_manager,
            role="support_manager",
            tenant=self.master_tenant,
        )

        # Technicians in Master Tenant
        self.tech_dave = User.objects.create_user(
            username="tech_dave",
            email="dave@master.com",
            tenant=self.master_tenant,
        )
        SupportMembership.objects.create(
            user=self.tech_dave,
            role="technician",
            tenant=self.master_tenant,
        )

        self.tech_sarah = User.objects.create_user(
            username="tech_sarah",
            email="sarah@master.com",
            tenant=self.master_tenant,
        )
        SupportMembership.objects.create(
            user=self.tech_sarah,
            role="technician",
            tenant=self.master_tenant,
        )

        # Customer User in Tenant Alpha
        self.customer_user = User.objects.create_user(
            username="customer_alice",
            email="alice@alpha.com",
            tenant=self.tenant_alpha,
        )

        # Tickets in Tenant Alpha
        self.ticket_1 = Ticket.objects.create(
            title="Sensor Anomaly",
            description="Vibration spikes detected",
            tenant=self.tenant_alpha,
            workspace=self.ws_alpha,
            user=self.customer_user,
            assigned_to=self.support_manager,
        )
        self.ticket_2 = Ticket.objects.create(
            title="Gateway Offline",
            description="Gateway 2 unresponsive",
            tenant=self.tenant_alpha,
            workspace=self.ws_alpha,
            user=self.customer_user,
            assigned_to=self.support_manager,
        )

    def test_ticket_delegation_assigns_technician_and_logs_audit(self):
        """Support manager delegates ticket to technician; assigned_to updates and auditlog records change."""
        self.client.force_authenticate(user=self.support_manager)
        response = self.client.post(
            f"/api/v1/support/tickets/{self.ticket_1.id}/delegate/",
            {"assigned_to_id": self.tech_dave.id},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "ticket_delegated")

        self.ticket_1.refresh_from_db()
        self.assertEqual(self.ticket_1.assigned_to, self.tech_dave)

        # Verify auditlog entry
        audit_entry = LogEntry.objects.filter(
            object_pk=str(self.ticket_1.id),
            actor=self.support_manager,
            action=LogEntry.Action.UPDATE,
        ).last()
        self.assertIsNotNone(audit_entry)
        self.assertEqual(audit_entry.additional_data.get("action_detail"), "ticket_delegated")
        self.assertEqual(audit_entry.additional_data.get("new_assignee"), str(self.tech_dave.id))

    def test_assigned_technician_cross_tenant_access_and_update(self):
        """Assigned technician without tenant membership can retrieve and update assigned customer ticket."""
        self.ticket_1.assigned_to = self.tech_dave
        self.ticket_1.save()

        self.client.force_authenticate(user=self.tech_dave)

        # Retrieve ticket
        get_resp = self.client.get(f"/api/v1/support/tickets/{self.ticket_1.id}/")
        self.assertEqual(get_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(get_resp.data["title"], "Sensor Anomaly")

        # Update status
        patch_resp = self.client.patch(
            f"/api/v1/support/tickets/{self.ticket_1.id}/",
            {"status": "in_progress"},
            format="json",
        )
        self.assertEqual(patch_resp.status_code, status.HTTP_200_OK)
        self.ticket_1.refresh_from_db()
        self.assertEqual(self.ticket_1.status, "in_progress")

        # Add comment
        comment_resp = self.client.post(
            "/api/v1/support/comments/",
            {
                "ticket": str(self.ticket_1.id),
                "content": "Diagnostic in progress by Technician Dave",
                "response": True,
            },
            format="json",
        )
        self.assertEqual(comment_resp.status_code, status.HTTP_201_CREATED)

    def test_assigned_technician_denied_access_to_unassigned_customer_tickets(self):
        """Technician Dave assigned to ticket 1 is strictly denied access to ticket 2 in same customer tenant."""
        self.ticket_1.assigned_to = self.tech_dave
        self.ticket_1.save()
        self.ticket_2.assigned_to = self.tech_sarah
        self.ticket_2.save()

        self.client.force_authenticate(user=self.tech_dave)
        response = self.client.get(f"/api/v1/support/tickets/{self.ticket_2.id}/")
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_ticket_reassignment_immediately_terminates_previous_technician_access(self):
        """Reassigning ticket to Sarah immediately terminates Dave's access to that ticket."""
        self.ticket_1.assigned_to = self.tech_dave
        self.ticket_1.save()

        # Dave currently has access
        self.client.force_authenticate(user=self.tech_dave)
        resp = self.client.get(f"/api/v1/support/tickets/{self.ticket_1.id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        # Support manager reassigns to Sarah
        self.client.force_authenticate(user=self.support_manager)
        del_resp = self.client.post(
            f"/api/v1/support/tickets/{self.ticket_1.id}/delegate/",
            {"assigned_to_id": self.tech_sarah.id},
            format="json",
        )
        self.assertEqual(del_resp.status_code, status.HTTP_200_OK)

        # Dave is now denied
        self.client.force_authenticate(user=self.tech_dave)
        denied_resp = self.client.get(f"/api/v1/support/tickets/{self.ticket_1.id}/")
        self.assertIn(denied_resp.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

        patch_denied = self.client.patch(
            f"/api/v1/support/tickets/{self.ticket_1.id}/",
            {"status": "resolved"},
            format="json",
        )
        self.assertIn(patch_denied.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_grant_diagnostic_pass_creates_assignment_and_auditlog(self):
        """Support manager issues diagnostic pass with TTL; pass is created and audit trail is recorded."""
        self.client.force_authenticate(user=self.support_manager)
        response = self.client.post(
            f"/api/v1/support/tickets/{self.ticket_1.id}/grant_diagnostic_pass/",
            {
                "technician_id": self.tech_dave.id,
                "workspace_id": self.ws_alpha.id,
                "duration_hours": 4,
                "reason": "Deep telemetry sensor investigation",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        pass_id = response.data["id"]
        self.assertEqual(response.data["status"], "ACTIVE")
        self.assertTrue(response.data["is_valid"])

        # Verify DB record
        pass_obj = TechnicianAssignment.objects.get(id=pass_id)
        self.assertEqual(pass_obj.technician, self.tech_dave)
        self.assertEqual(pass_obj.workspace, self.ws_alpha)
        self.assertEqual(pass_obj.granted_by, self.support_manager)
        self.assertTrue(pass_obj.is_valid())

        # Verify audit trail
        audit_entry = LogEntry.objects.filter(
            object_pk=str(pass_obj.pk),
            actor=self.support_manager,
            action=LogEntry.Action.CREATE,
        ).first()
        self.assertIsNotNone(audit_entry)

    def test_active_diagnostic_pass_grants_read_only_access_and_rejects_mutation(self):
        """Active pass grants GET on customer devices and machines, but rejects DELETE/destructive operations."""
        # Create active diagnostic pass for Dave
        TechnicianAssignment.objects.create(
            technician=self.tech_dave,
            ticket=self.ticket_1,
            workspace=self.ws_alpha,
            granted_by=self.support_manager,
            expires_at=timezone.now() + timedelta(hours=4),
            status="ACTIVE",
            reason="Investigating devices",
        )

        self.client.force_authenticate(user=self.tech_dave)

        # GET devices permitted
        get_dev_resp = self.client.get(
            "/api/v1/infrastructure/devices/",
            HTTP_X_WORKSPACE_ID=str(self.ws_alpha.id),
        )
        self.assertEqual(get_dev_resp.status_code, status.HTTP_200_OK)

        # GET machines permitted
        get_mach_resp = self.client.get(
            "/api/v1/infrastructure/machines/",
            HTTP_X_WORKSPACE_ID=str(self.ws_alpha.id),
        )
        self.assertEqual(get_mach_resp.status_code, status.HTTP_200_OK)

        # DELETE device denied (pass is read-only)
        del_resp = self.client.delete(
            f"/api/v1/infrastructure/devices/{self.device_alpha.id}/",
            HTTP_X_WORKSPACE_ID=str(self.ws_alpha.id),
        )
        self.assertEqual(del_resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Device.objects.filter(id=self.device_alpha.id).exists())

    def test_expired_pass_immediately_denies_workspace_access(self):
        """Pass where expires_at is in the past immediately denies workspace infrastructure access."""
        TechnicianAssignment.objects.create(
            technician=self.tech_dave,
            ticket=self.ticket_1,
            workspace=self.ws_alpha,
            granted_by=self.support_manager,
            expires_at=timezone.now() - timedelta(minutes=10),
            status="ACTIVE",
            reason="Expired pass",
        )

        self.client.force_authenticate(user=self.tech_dave)
        resp = self.client.get(
            "/api/v1/infrastructure/devices/",
            HTTP_X_WORKSPACE_ID=str(self.ws_alpha.id),
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_administrative_revocation_terminates_pass(self):
        """Support manager can explicitly revoke an active diagnostic pass, immediately terminating access."""
        diag_pass = TechnicianAssignment.objects.create(
            technician=self.tech_dave,
            ticket=self.ticket_1,
            workspace=self.ws_alpha,
            granted_by=self.support_manager,
            expires_at=timezone.now() + timedelta(hours=2),
            status="ACTIVE",
            reason="Revocation test pass",
        )

        # Dave initially has access
        self.client.force_authenticate(user=self.tech_dave)
        resp_before = self.client.get(
            "/api/v1/infrastructure/devices/",
            HTTP_X_WORKSPACE_ID=str(self.ws_alpha.id),
        )
        self.assertEqual(resp_before.status_code, status.HTTP_200_OK)

        # Manager revokes pass
        self.client.force_authenticate(user=self.support_manager)
        revoke_resp = self.client.post(
            f"/api/v1/support/tickets/{self.ticket_1.id}/revoke_diagnostic_pass/",
            {"pass_id": diag_pass.id},
            format="json",
        )
        self.assertEqual(revoke_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(revoke_resp.data["status"], "pass_revoked")

        diag_pass.refresh_from_db()
        self.assertEqual(diag_pass.status, "REVOKED")
        self.assertFalse(diag_pass.is_valid())

        # Dave is now denied
        self.client.force_authenticate(user=self.tech_dave)
        resp_after = self.client.get(
            "/api/v1/infrastructure/devices/",
            HTTP_X_WORKSPACE_ID=str(self.ws_alpha.id),
        )
        self.assertEqual(resp_after.status_code, status.HTTP_403_FORBIDDEN)

    def test_ticket_resolution_auto_revokes_active_diagnostic_passes(self):
        """Updating ticket status to 'resolved' automatically revokes all associated active diagnostic passes."""
        diag_pass = TechnicianAssignment.objects.create(
            technician=self.tech_dave,
            ticket=self.ticket_1,
            workspace=self.ws_alpha,
            granted_by=self.support_manager,
            expires_at=timezone.now() + timedelta(hours=4),
            status="ACTIVE",
            reason="Auto revoke test",
        )
        self.ticket_1.assigned_to = self.tech_dave
        self.ticket_1.save()

        # Dave has workspace access
        self.client.force_authenticate(user=self.tech_dave)
        resp = self.client.get(
            "/api/v1/infrastructure/devices/",
            HTTP_X_WORKSPACE_ID=str(self.ws_alpha.id),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        # Dave resolves ticket
        patch_resp = self.client.patch(
            f"/api/v1/support/tickets/{self.ticket_1.id}/",
            {"status": "resolved"},
            format="json",
        )
        self.assertEqual(patch_resp.status_code, status.HTTP_200_OK)

        diag_pass.refresh_from_db()
        self.assertEqual(diag_pass.status, "REVOKED")
        self.assertFalse(diag_pass.is_valid())

        # Diagnostic access terminated
        resp_post_resolve = self.client.get(
            "/api/v1/infrastructure/devices/",
            HTTP_X_WORKSPACE_ID=str(self.ws_alpha.id),
        )
        self.assertEqual(resp_post_resolve.status_code, status.HTTP_403_FORBIDDEN)

        # Auditlog captures pass status transition
        audit_entry = LogEntry.objects.filter(
            object_pk=str(diag_pass.pk),
            action=LogEntry.Action.UPDATE,
        ).last()
        self.assertIsNotNone(audit_entry)
        self.assertEqual(audit_entry.additional_data.get("action_detail"), "auto_revocation_on_ticket_closure")

    def test_unauthorized_user_cannot_grant_diagnostic_pass(self):
        """Customer user without support manager role cannot grant diagnostic passes."""
        self.client.force_authenticate(user=self.customer_user)
        response = self.client.post(
            f"/api/v1/support/tickets/{self.ticket_1.id}/grant_diagnostic_pass/",
            {
                "technician_id": self.tech_dave.id,
                "workspace_id": self.ws_alpha.id,
                "duration_hours": 4,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_reactivation_of_revoked_pass_prohibited(self):
        """TechnicianAssignment clean() prevents reactivating an expired or revoked pass."""
        diag_pass = TechnicianAssignment.objects.create(
            technician=self.tech_dave,
            ticket=self.ticket_1,
            workspace=self.ws_alpha,
            granted_by=self.support_manager,
            expires_at=timezone.now() + timedelta(hours=1),
            status="REVOKED",
            reason="Revoked pass",
        )

        diag_pass.status = "ACTIVE"
        with self.assertRaises(ValidationError):
            diag_pass.clean()
