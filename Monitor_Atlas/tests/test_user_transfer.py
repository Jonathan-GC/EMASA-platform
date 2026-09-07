from unittest.mock import patch
from django.test import TestCase
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient
from rest_framework import status
from guardian.shortcuts import assign_perm, get_perms
from auditlog.models import LogEntry

from organizations.models import Tenant, Workspace, Subscription
from organizations.helpers import (
    get_or_create_default_workspace,
    get_no_role,
    get_or_create_admin_role,
)
from roles.models import Role, WorkspaceMembership
from roles.helpers import get_global_admin_role_group
from users.models import User
from users.services import UserTenantTransferService
from chirpstack.models import ApiUser


class UserTenantTransferServiceTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.subscription = Subscription.objects.create(
            name="Transfer Test Plan",
            description="Subscription for transfer tests",
        )
        self.global_tenant = Tenant.objects.create(
            name="Global Tenant",
            subscription=self.subscription,
            is_global=True,
        )
        self.tenant_source = Tenant.objects.create(
            name="Source Tenant Alpha",
            subscription=self.subscription,
            is_global=False,
            cs_tenant_id="cs-tenant-alpha-uuid",
        )
        self.tenant_dest = Tenant.objects.create(
            name="Destination Tenant Beta",
            subscription=self.subscription,
            is_global=False,
            cs_tenant_id="cs-tenant-beta-uuid",
        )

        # Workspaces
        self.ws_source = Workspace.objects.create(
            name="Source WS", tenant=self.tenant_source
        )

        # Target user in source tenant
        self.target_user = User.objects.create_user(
            username="transfer_user",
            email="transfer_user@test.com",
            tenant=self.tenant_source,
        )

        # Create role and membership in source workspace
        self.role_source = Role.objects.create(
            workspace=self.ws_source,
            name="Source Analyst",
        )
        self.membership_source = WorkspaceMembership.objects.create(
            workspace=self.ws_source,
            user=self.target_user,
            role=self.role_source,
        )

        # Assign direct object-level permissions in source tenant
        assign_perm("view_tenant", self.target_user, self.tenant_source)
        assign_perm("view_workspace", self.target_user, self.ws_source)

        # Admin user
        self.admin_user = User.objects.create_superuser(
            username="admin_initiator",
            email="admin_init@test.com",
            tenant=self.global_tenant,
        )

        # Non-admin regular user
        self.regular_user = User.objects.create_user(
            username="regular_unauthorized",
            email="regular@test.com",
            tenant=self.tenant_source,
        )

    def test_complete_transfer_lifecycle(self):
        """
        Verify complete transfer lifecycle: source memberships deleted,
        role groups removed, Guardian permissions purged, default workspace
        and "Sin rol" assigned in destination, and tenant updated.
        """
        # Ensure initial state
        self.assertIn(self.role_source.group, self.target_user.groups.all())
        self.assertIn("view_tenant", get_perms(self.target_user, self.tenant_source))
        self.assertIn("view_workspace", get_perms(self.target_user, self.ws_source))

        result = UserTenantTransferService.transfer_user(
            user=self.target_user,
            destination_tenant=self.tenant_dest,
            actor=self.admin_user,
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["user_id"], str(self.target_user.id))
        self.assertEqual(result["tenant_id"], str(self.tenant_dest.id))

        self.target_user.refresh_from_db()
        # 1. Tenant updated
        self.assertEqual(self.target_user.tenant, self.tenant_dest)

        # 2. Source workspace memberships purged
        self.assertFalse(
            WorkspaceMembership.objects.filter(
                user=self.target_user, workspace__tenant=self.tenant_source
            ).exists()
        )

        # 3. Source role groups disassociated
        self.assertNotIn(self.role_source.group, self.target_user.groups.all())

        # 4. Direct Guardian permissions purged from source
        self.assertNotIn("view_tenant", get_perms(self.target_user, self.tenant_source))
        self.assertNotIn("view_workspace", get_perms(self.target_user, self.ws_source))

        # 5. Destination default workspace and "Sin rol" assigned
        dest_membership = WorkspaceMembership.objects.filter(
            user=self.target_user, workspace__tenant=self.tenant_dest
        ).first()
        self.assertIsNotNone(dest_membership)
        self.assertEqual(dest_membership.role.name, "Sin rol")

        # 6. Base user permissions initialized for destination tenant
        self.assertIn("view_tenant", get_perms(self.target_user, self.tenant_dest))

    def test_rejection_of_transfer_to_identical_tenant(self):
        """Transfer must be rejected when source and destination are the same tenant."""
        with self.assertRaises(ValidationError) as ctx:
            UserTenantTransferService.transfer_user(
                user=self.target_user,
                destination_tenant=self.tenant_source,
                actor=self.admin_user,
            )
        self.assertIn("identical", str(ctx.exception).lower())

    def test_audit_log_record_creation(self):
        """Immutable audit log record must capture actor, target, source, and destination."""
        result = UserTenantTransferService.transfer_user(
            user=self.target_user,
            destination_tenant=self.tenant_dest,
            actor=self.admin_user,
        )

        log_entry = LogEntry.objects.get(id=result["audit_log_id"])
        self.assertEqual(log_entry.actor, self.admin_user)
        self.assertEqual(log_entry.object_pk, str(self.target_user.pk))
        self.assertEqual(log_entry.additional_data["source_tenant_id"], str(self.tenant_source.id))
        self.assertEqual(log_entry.additional_data["source_tenant_name"], self.tenant_source.name)
        self.assertEqual(log_entry.additional_data["destination_tenant_id"], str(self.tenant_dest.id))
        self.assertEqual(log_entry.additional_data["destination_tenant_name"], self.tenant_dest.name)
        self.assertEqual(log_entry.additional_data["actor_id"], str(self.admin_user.id))
        self.assertEqual(log_entry.additional_data["target_user_id"], str(self.target_user.id))
        self.assertIsNotNone(log_entry.timestamp)

    def test_chirpstack_sync_success(self):
        """When ApiUser is linked, ChirpStack sync is invoked and status set to SYNCED."""
        api_user = ApiUser.objects.create(
            email=self.target_user.email,
            workspace=self.ws_source,
            cs_user_id="cs-user-12345",
        )

        with patch("users.services.sync_api_user_update") as mock_sync:
            def fake_sync(au):
                au.sync_status = "SYNCED"
                au.sync_error = ""
                au.save()

            mock_sync.side_effect = fake_sync

            result = UserTenantTransferService.transfer_user(
                user=self.target_user,
                destination_tenant=self.tenant_dest,
                actor=self.admin_user,
            )

            self.assertTrue(result["chirpstack_synced"])
            api_user.refresh_from_db()
            self.assertEqual(api_user.sync_status, "SYNCED")
            self.assertEqual(api_user.workspace.tenant, self.tenant_dest)

    def test_chirpstack_sync_failure_does_not_rollback_database(self):
        """External ChirpStack error records ERROR in ApiUser while DB transaction commits."""
        api_user = ApiUser.objects.create(
            email=self.target_user.email,
            workspace=self.ws_source,
            cs_user_id="cs-user-54321",
        )

        with patch("users.services.sync_api_user_update") as mock_sync:
            mock_sync.side_effect = Exception("ChirpStack API timeout: 504 Gateway Timeout")

            result = UserTenantTransferService.transfer_user(
                user=self.target_user,
                destination_tenant=self.tenant_dest,
                actor=self.admin_user,
            )

            self.assertFalse(result["chirpstack_synced"])

            # Local DB transaction MUST commit successfully
            self.target_user.refresh_from_db()
            self.assertEqual(self.target_user.tenant, self.tenant_dest)

            api_user.refresh_from_db()
            self.assertEqual(api_user.sync_status, "ERROR")
            self.assertIn("504 Gateway Timeout", api_user.sync_error)
            self.assertEqual(api_user.workspace.tenant, self.tenant_dest)

    def test_transactional_rollback_on_unexpected_database_error(self):
        """If a database error occurs during transfer, entire state rolls back."""
        with patch("users.services.assign_new_user_base_permissions") as mock_base_perms:
            mock_base_perms.side_effect = RuntimeError("Fatal DB deadlock simulated")

            with self.assertRaises(RuntimeError):
                UserTenantTransferService.transfer_user(
                    user=self.target_user,
                    destination_tenant=self.tenant_dest,
                    actor=self.admin_user,
                )

            # Assert rollback: user stays in source tenant
            self.target_user.refresh_from_db()
            self.assertEqual(self.target_user.tenant, self.tenant_source)

            # Source membership still intact
            self.assertTrue(
                WorkspaceMembership.objects.filter(
                    user=self.target_user, workspace=self.ws_source
                ).exists()
            )

            # Role group still attached
            self.assertIn(self.role_source.group, self.target_user.groups.all())


class UserTransferEndpointTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.subscription = Subscription.objects.create(name="Endpoint Test Plan")
        self.global_tenant = Tenant.objects.create(
            name="Global Endpoint Tenant",
            subscription=self.subscription,
            is_global=True,
        )
        self.tenant_source = Tenant.objects.create(
            name="Source Endpoint Tenant",
            subscription=self.subscription,
        )
        self.tenant_dest = Tenant.objects.create(
            name="Destination Endpoint Tenant",
            subscription=self.subscription,
        )

        self.target_user = User.objects.create_user(
            username="endpoint_target",
            email="endpoint_target@test.com",
            tenant=self.tenant_source,
        )

        # Superuser / Admin
        self.admin = User.objects.create_superuser(
            username="admin_api",
            email="admin_api@test.com",
            tenant=self.global_tenant,
        )

        # Regular user
        self.regular = User.objects.create_user(
            username="regular_api",
            email="regular_api@test.com",
            tenant=self.tenant_source,
        )

        self.url = f"/api/v1/users/{self.target_user.id}/transfer_tenant/"

    def test_endpoint_successful_transfer(self):
        """Admin user can successfully transfer user to destination tenant via HTTP POST."""
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            self.url,
            {"destination_tenant_id": str(self.tenant_dest.id)},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["user_id"], str(self.target_user.id))
        self.assertEqual(data["tenant_id"], str(self.tenant_dest.id))

        self.target_user.refresh_from_db()
        self.assertEqual(self.target_user.tenant, self.tenant_dest)

    def test_endpoint_rejection_identical_tenant(self):
        """Endpoint rejects transfer when source and destination are identical (HTTP 400)."""
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            self.url,
            {"destination_tenant_id": str(self.tenant_source.id)},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.json())

    def test_endpoint_rejection_nonexistent_destination_tenant(self):
        """Endpoint rejects transfer when destination tenant does not exist (HTTP 404)."""
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            self.url,
            {"destination_tenant_id": "nonexistent_tenant_999"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_endpoint_rejection_unauthorized_user(self):
        """Unauthorized non-admin user is rejected with HTTP 403 Forbidden."""
        self.client.force_authenticate(user=self.regular)
        response = self.client.post(
            self.url,
            {"destination_tenant_id": str(self.tenant_dest.id)},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
