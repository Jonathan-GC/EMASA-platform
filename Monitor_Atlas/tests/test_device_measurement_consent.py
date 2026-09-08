from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from django.db import IntegrityError, transaction
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient
from rest_framework import status
from guardian.shortcuts import assign_perm
from auditlog.models import LogEntry

from organizations.models import Tenant, Workspace, Subscription
from roles.models import Role, WorkspaceMembership
from users.models import User
from chirpstack.models import DeviceProfile
from infrastructure.models import Machine, Device, Application, Type, Measurements, DeviceConsent
from infrastructure.consent_helpers import (
    canonical_consent_payload,
    compute_device_consent_signature,
    verify_device_consent_signature,
)
from infrastructure.serializers import (
    MeasurementsSerializer,
    ConsentAcceptSerializer,
)


class DeviceMeasurementConsentTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.subscription = Subscription.objects.create(name="Sub", description="Sub")

        # Tenants
        self.tenant_1 = Tenant.objects.create(
            name="Tenant 1", subscription=self.subscription, is_global=False
        )
        self.tenant_2 = Tenant.objects.create(
            name="Tenant 2", subscription=self.subscription, is_global=False
        )

        # Workspaces
        self.ws_1 = Workspace.objects.create(name="WS 1", tenant=self.tenant_1)
        self.ws_2 = Workspace.objects.create(name="WS 2", tenant=self.tenant_2)

        # Infrastructure in WS 1
        self.app_1 = Application.objects.create(name="App 1", workspace=self.ws_1)
        self.dp_1 = DeviceProfile.objects.create(
            name="Profile 1",
            workspace=self.ws_1,
            region="US915",
            abp_rx1_delay=1,
            abp_rx1_dr_offset=0,
            abp_rx2_dr=0,
            abp_rx2_freq=923300000,
        )
        self.dev_type = Type.objects.create(name="Vibration Sensor")
        self.device_1 = Device.objects.create(
            dev_eui="AABBCCDDEEFF0001",
            name="Device 1",
            description="Test Sensor 1",
            workspace=self.ws_1,
            application=self.app_1,
            device_profile=self.dp_1,
            device_type=self.dev_type,
        )
        self.m1 = Measurements.objects.create(
            device=self.device_1,
            min=0.0,
            max=100.0,
            threshold=50.0,
            unit="C",
            label="Temperature",
            require_consent=True,
        )
        self.m2 = Measurements.objects.create(
            device=self.device_1,
            min=0.0,
            max=10.0,
            threshold=5.0,
            unit="g",
            label="Vibration",
            require_consent=True,
        )

        # Infrastructure in WS 2
        self.app_2 = Application.objects.create(name="App 2", workspace=self.ws_2)
        self.dp_2 = DeviceProfile.objects.create(
            name="Profile 2",
            workspace=self.ws_2,
            region="US915",
            abp_rx1_delay=1,
            abp_rx1_dr_offset=0,
            abp_rx2_dr=0,
            abp_rx2_freq=923300000,
        )
        self.device_2 = Device.objects.create(
            dev_eui="AABBCCDDEEFF0002",
            name="Device 2",
            description="Test Sensor 2",
            workspace=self.ws_2,
            application=self.app_2,
            device_profile=self.dp_2,
            device_type=self.dev_type,
        )
        self.m_other = Measurements.objects.create(
            device=self.device_2,
            min=0.0,
            max=100.0,
            threshold=50.0,
            unit="bar",
            label="Pressure",
            require_consent=True,
        )

        # Roles and Users
        from django.contrib.auth.models import Group

        self.group_admin = Group.objects.create(name="ws_admin_group")
        self.role_admin = Role.objects.create(
            name="Workspace Admin", workspace=self.ws_1, group=self.group_admin
        )
        assign_perm("infrastructure.view_device", self.group_admin)
        assign_perm("infrastructure.change_device", self.group_admin)
        assign_perm("infrastructure.view_device", self.group_admin, self.device_1)
        assign_perm("infrastructure.change_device", self.group_admin, self.device_1)
        assign_perm("infrastructure.view_deviceconsent", self.group_admin)
        assign_perm("infrastructure.add_deviceconsent", self.group_admin)
        assign_perm("infrastructure.change_deviceconsent", self.group_admin)

        self.user_admin = User.objects.create_user(
            username="ws_admin", email="admin@tenant1.com", tenant=self.tenant_1
        )
        WorkspaceMembership.objects.create(
            user=self.user_admin, workspace=self.ws_1, role=self.role_admin
        )

        # Viewer User (only view_device, view_deviceconsent)
        self.group_viewer = Group.objects.create(name="ws_viewer_group")
        self.role_viewer = Role.objects.create(
            name="Workspace Viewer", workspace=self.ws_1, group=self.group_viewer
        )
        assign_perm("infrastructure.view_device", self.group_viewer)
        assign_perm("infrastructure.view_device", self.group_viewer, self.device_1)
        assign_perm("infrastructure.view_deviceconsent", self.group_viewer)

        self.user_viewer = User.objects.create_user(
            username="ws_viewer", email="viewer@tenant1.com", tenant=self.tenant_1
        )
        WorkspaceMembership.objects.create(
            user=self.user_viewer, workspace=self.ws_1, role=self.role_viewer
        )

        # Foreign User (Tenant 2)
        self.user_foreign = User.objects.create_user(
            username="foreign_user", email="user@tenant2.com", tenant=self.tenant_2
        )

    def test_measurement_default_require_consent(self):
        """Newly created measurement defaults require_consent to True and serializes properly."""
        m = Measurements.objects.create(
            device=self.device_1,
            min=0.0,
            max=50.0,
            threshold=25.0,
            unit="V",
            label="Voltage",
        )
        self.assertTrue(m.require_consent)

        # Exemption
        m_exempt = Measurements.objects.create(
            device=self.device_1,
            min=0.0,
            max=50.0,
            threshold=25.0,
            unit="Hz",
            label="Frequency",
            require_consent=False,
        )
        self.assertFalse(m_exempt.require_consent)

        # Serialization
        serializer = MeasurementsSerializer(m)
        self.assertIn("require_consent", serializer.data)
        self.assertTrue(serializer.data["require_consent"])

    def test_device_consent_model_partial_unique_constraint(self):
        """Database enforces at most one ACTIVE consent per device."""
        DeviceConsent.objects.create(
            device=self.device_1,
            tenant=self.tenant_1,
            workspace=self.ws_1,
            version=1,
            status="ACTIVE",
            terms_version="v1.0",
            device_signature="dummy_signature_1",
            granted_by=self.user_admin,
        )

        # Creating a second ACTIVE consent for the same device must fail with IntegrityError
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                DeviceConsent.objects.create(
                    device=self.device_1,
                    tenant=self.tenant_1,
                    workspace=self.ws_1,
                    version=2,
                    status="ACTIVE",
                    terms_version="v1.0",
                    device_signature="dummy_signature_2",
                    granted_by=self.user_admin,
                )

        # Non-ACTIVE consents do not violate constraint
        c_superseded = DeviceConsent.objects.create(
            device=self.device_1,
            tenant=self.tenant_1,
            workspace=self.ws_1,
            version=2,
            status="SUPERSEDED",
            terms_version="v1.0",
            device_signature="dummy_signature_3",
            granted_by=self.user_admin,
        )
        self.assertIsNotNone(c_superseded.id)

    def test_device_boundary_validation(self):
        """Consent cannot associate measurements belonging to other devices."""
        consent = DeviceConsent.objects.create(
            device=self.device_1,
            tenant=self.tenant_1,
            workspace=self.ws_1,
            version=1,
            status="ACTIVE",
            terms_version="v1.0",
            device_signature="sig",
            granted_by=self.user_admin,
        )
        consent.consented_measurements.add(self.m_other)

        with self.assertRaises(ValidationError):
            consent.clean()

        # Serializer validation
        serializer = ConsentAcceptSerializer(
            data={"consented_measurement_ids": [str(self.m_other.id)], "terms_version": "v1.0"},
            context={"device": self.device_1},
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("consented_measurement_ids", serializer.errors)

    def test_cryptographic_signature_helpers(self):
        """Deterministic SHA-256 computation, sort-order invariance, and tamper detection."""
        now_iso = timezone.now().isoformat()

        # Sort order invariance
        sig1 = compute_device_consent_signature(
            device_eui=self.device_1.dev_eui,
            tenant_id=self.tenant_1.id,
            version=1,
            terms_version="v1.0",
            measurement_ids=[str(self.m2.id), str(self.m1.id)],
            granter_id=self.user_admin.id,
            granted_at_iso=now_iso,
        )
        sig2 = compute_device_consent_signature(
            device_eui=self.device_1.dev_eui,
            tenant_id=self.tenant_1.id,
            version=1,
            terms_version="v1.0",
            measurement_ids=[str(self.m1.id), str(self.m2.id)],
            granter_id=self.user_admin.id,
            granted_at_iso=now_iso,
        )
        self.assertEqual(len(sig1), 64)
        self.assertEqual(sig1, sig2)

        # Verification
        consent = DeviceConsent.objects.create(
            device=self.device_1,
            tenant=self.tenant_1,
            workspace=self.ws_1,
            version=1,
            status="ACTIVE",
            terms_version="v1.0",
            device_signature=sig1,
            granted_by=self.user_admin,
        )
        consent.consented_measurements.add(self.m1, self.m2)

        # Since auto_now_add sets granted_at on create, recalculate with actual granted_at
        sig_actual = compute_device_consent_signature(
            device_eui=self.device_1.dev_eui,
            tenant_id=self.tenant_1.id,
            version=1,
            terms_version="v1.0",
            measurement_ids=[str(self.m1.id), str(self.m2.id)],
            granter_id=self.user_admin.id,
            granted_at_iso=consent.granted_at.isoformat(),
        )
        consent.device_signature = sig_actual
        consent.save()

        self.assertTrue(verify_device_consent_signature(consent))

        # Tampering detected
        consent.terms_version = "v2.0_tampered"
        self.assertFalse(verify_device_consent_signature(consent))

    def test_api_get_active_consent(self):
        """GET /devices/{id}/consent/ returns active consent or 404."""
        self.client.force_authenticate(user=self.user_admin)

        # No active consent -> 404
        resp = self.client.get(
            f"/api/v1/infrastructure/devices/{self.device_1.id}/consent/",
            HTTP_X_WORKSPACE_ID=str(self.ws_1.id),
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

        # Create active consent
        consent = DeviceConsent.objects.create(
            device=self.device_1,
            tenant=self.tenant_1,
            workspace=self.ws_1,
            version=1,
            status="ACTIVE",
            terms_version="v1.0",
            device_signature="sig_test",
            granted_by=self.user_admin,
        )
        consent.consented_measurements.add(self.m1)

        resp = self.client.get(
            f"/api/v1/infrastructure/devices/{self.device_1.id}/consent/",
            HTTP_X_WORKSPACE_ID=str(self.ws_1.id),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["version"], 1)
        self.assertEqual(resp.data["status"], "ACTIVE")
        self.assertIn(str(self.m1.id), resp.data["consented_measurement_ids"])

    def test_api_accept_consent_initial_and_supersede(self):
        """POST /devices/{id}/consent/accept/ atomically supersedes prior consent and creates next version."""
        self.client.force_authenticate(user=self.user_admin)

        # Initial acceptance (v1)
        resp1 = self.client.post(
            f"/api/v1/infrastructure/devices/{self.device_1.id}/consent/accept/",
            {
                "consented_measurement_ids": [str(self.m1.id)],
                "terms_version": "v1.0",
            },
            format="json",
            HTTP_X_WORKSPACE_ID=str(self.ws_1.id),
        )
        self.assertEqual(resp1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp1.data["version"], 1)
        self.assertEqual(resp1.data["status"], "ACTIVE")
        self.assertEqual(len(resp1.data["device_signature"]), 64)
        c1_id = resp1.data["id"]

        c1 = DeviceConsent.objects.get(id=c1_id)
        self.assertEqual(c1.status, "ACTIVE")
        self.assertTrue(verify_device_consent_signature(c1))

        # Subsequent acceptance (v2) supersedes v1
        resp2 = self.client.post(
            f"/api/v1/infrastructure/devices/{self.device_1.id}/consent/accept/",
            {
                "consented_measurement_ids": [str(self.m1.id), str(self.m2.id)],
                "terms_version": "v1.1",
            },
            format="json",
            HTTP_X_WORKSPACE_ID=str(self.ws_1.id),
        )
        self.assertEqual(resp2.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp2.data["version"], 2)
        self.assertEqual(resp2.data["status"], "ACTIVE")
        self.assertEqual(resp2.data["terms_version"], "v1.1")

        c1.refresh_from_db()
        self.assertEqual(c1.status, "SUPERSEDED")

        c2 = DeviceConsent.objects.get(id=resp2.data["id"])
        self.assertEqual(c2.version, 2)
        self.assertEqual(c2.status, "ACTIVE")
        self.assertTrue(verify_device_consent_signature(c2))

    def test_api_revoke_consent_with_mandatory_reason(self):
        """POST /devices/{id}/consent/revoke/ enforces non-empty reason and transitions ACTIVE to REVOKED."""
        self.client.force_authenticate(user=self.user_admin)

        consent = DeviceConsent.objects.create(
            device=self.device_1,
            tenant=self.tenant_1,
            workspace=self.ws_1,
            version=1,
            status="ACTIVE",
            terms_version="v1.0",
            device_signature="sig",
            granted_by=self.user_admin,
        )

        # Missing reason -> 400
        resp_fail = self.client.post(
            f"/api/v1/infrastructure/devices/{self.device_1.id}/consent/revoke/",
            {"reason": ""},
            format="json",
            HTTP_X_WORKSPACE_ID=str(self.ws_1.id),
        )
        self.assertEqual(resp_fail.status_code, status.HTTP_400_BAD_REQUEST)
        consent.refresh_from_db()
        self.assertEqual(consent.status, "ACTIVE")

        # Valid revocation
        resp_ok = self.client.post(
            f"/api/v1/infrastructure/devices/{self.device_1.id}/consent/revoke/",
            {"reason": "Tenant opt-out for AI model training."},
            format="json",
            HTTP_X_WORKSPACE_ID=str(self.ws_1.id),
        )
        self.assertEqual(resp_ok.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_ok.data["status"], "consent_revoked")

        consent.refresh_from_db()
        self.assertEqual(consent.status, "REVOKED")
        self.assertEqual(consent.revoked_by, self.user_admin)
        self.assertIsNotNone(consent.revoked_at)
        self.assertEqual(consent.revocation_reason, "Tenant opt-out for AI model training.")

        # Revoking when no active consent exists -> 400
        resp_no_active = self.client.post(
            f"/api/v1/infrastructure/devices/{self.device_1.id}/consent/revoke/",
            {"reason": "Another reason"},
            format="json",
            HTTP_X_WORKSPACE_ID=str(self.ws_1.id),
        )
        self.assertEqual(resp_no_active.status_code, status.HTTP_400_BAD_REQUEST)

    def test_api_consent_history(self):
        """GET /devices/{id}/consent/history/ returns chronological consent records."""
        self.client.force_authenticate(user=self.user_admin)

        c1 = DeviceConsent.objects.create(
            device=self.device_1,
            tenant=self.tenant_1,
            workspace=self.ws_1,
            version=1,
            status="SUPERSEDED",
            terms_version="v1.0",
            device_signature="sig1",
            granted_by=self.user_admin,
        )
        c2 = DeviceConsent.objects.create(
            device=self.device_1,
            tenant=self.tenant_1,
            workspace=self.ws_1,
            version=2,
            status="ACTIVE",
            terms_version="v1.1",
            device_signature="sig2",
            granted_by=self.user_admin,
        )

        resp = self.client.get(
            f"/api/v1/infrastructure/devices/{self.device_1.id}/consent/history/",
            HTTP_X_WORKSPACE_ID=str(self.ws_1.id),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 2)
        self.assertEqual(resp.data[0]["version"], 2)
        self.assertEqual(resp.data[1]["version"], 1)

    def test_api_consents_viewset_tenant_scoped_and_filtered(self):
        """GET /consents/ returns tenant-scoped consent list and supports filtering."""
        c1 = DeviceConsent.objects.create(
            device=self.device_1,
            tenant=self.tenant_1,
            workspace=self.ws_1,
            version=1,
            status="ACTIVE",
            terms_version="v1.0",
            device_signature="sig_t1",
            granted_by=self.user_admin,
        )
        c_foreign = DeviceConsent.objects.create(
            device=self.device_2,
            tenant=self.tenant_2,
            workspace=self.ws_2,
            version=1,
            status="ACTIVE",
            terms_version="v2.0",
            device_signature="sig_t2",
            granted_by=self.user_foreign,
        )

        self.client.force_authenticate(user=self.user_admin)

        # List consents in Tenant 1
        resp = self.client.get(
            "/api/v1/infrastructure/consents/",
            HTTP_X_WORKSPACE_ID=str(self.ws_1.id),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        results = resp.data if isinstance(resp.data, list) else resp.data.get("results", [])
        ids = [item["id"] for item in results]
        self.assertIn(str(c1.id), ids)
        self.assertNotIn(str(c_foreign.id), ids)

        # Filter by status
        resp_filtered = self.client.get(
            "/api/v1/infrastructure/consents/?status=ACTIVE",
            HTTP_X_WORKSPACE_ID=str(self.ws_1.id),
        )
        self.assertEqual(resp_filtered.status_code, status.HTTP_200_OK)
        results_filtered = (
            resp_filtered.data
            if isinstance(resp_filtered.data, list)
            else resp_filtered.data.get("results", [])
        )
        self.assertEqual(len(results_filtered), 1)

    def test_contextual_permissions_enforcement(self):
        """HasContextualPermission enforces view vs change permissions and blocks cross-tenant access."""
        consent = DeviceConsent.objects.create(
            device=self.device_1,
            tenant=self.tenant_1,
            workspace=self.ws_1,
            version=1,
            status="ACTIVE",
            terms_version="v1.0",
            device_signature="sig",
            granted_by=self.user_admin,
        )

        # Viewer can GET active consent
        self.client.force_authenticate(user=self.user_viewer)
        resp_view = self.client.get(
            f"/api/v1/infrastructure/devices/{self.device_1.id}/consent/",
            HTTP_X_WORKSPACE_ID=str(self.ws_1.id),
        )
        self.assertEqual(resp_view.status_code, status.HTTP_200_OK)

        # Viewer CANNOT accept consent (requires add_deviceconsent/change_deviceconsent)
        resp_accept_denied = self.client.post(
            f"/api/v1/infrastructure/devices/{self.device_1.id}/consent/accept/",
            {"terms_version": "v1.0"},
            format="json",
            HTTP_X_WORKSPACE_ID=str(self.ws_1.id),
        )
        self.assertEqual(resp_accept_denied.status_code, status.HTTP_403_FORBIDDEN)

        # Viewer CANNOT revoke consent (requires change_deviceconsent)
        resp_revoke_denied = self.client.post(
            f"/api/v1/infrastructure/devices/{self.device_1.id}/consent/revoke/",
            {"reason": "Denied attempt"},
            format="json",
            HTTP_X_WORKSPACE_ID=str(self.ws_1.id),
        )
        self.assertEqual(resp_revoke_denied.status_code, status.HTTP_403_FORBIDDEN)

        # Foreign user from Tenant 2 receives 404 or 403 on Tenant 1 device
        self.client.force_authenticate(user=self.user_foreign)
        resp_cross_tenant = self.client.get(
            f"/api/v1/infrastructure/devices/{self.device_1.id}/consent/",
            HTTP_X_WORKSPACE_ID=str(self.ws_2.id),
        )
        self.assertIn(resp_cross_tenant.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_audit_log_tracking_for_consent_lifecycle(self):
        """Auditlog captures consent creation, supersession, and revocation."""
        self.client.force_authenticate(user=self.user_admin)

        # 1. Accept initial consent
        resp1 = self.client.post(
            f"/api/v1/infrastructure/devices/{self.device_1.id}/consent/accept/",
            {"terms_version": "v1.0", "consented_measurement_ids": [str(self.m1.id)]},
            format="json",
            HTTP_X_WORKSPACE_ID=str(self.ws_1.id),
        )
        self.assertEqual(resp1.status_code, status.HTTP_201_CREATED)
        c1_id = resp1.data["id"]

        audit_create = LogEntry.objects.filter(
            object_pk=str(c1_id),
            action=LogEntry.Action.CREATE,
        ).first()
        self.assertIsNotNone(audit_create)
        self.assertEqual(audit_create.actor, self.user_admin)

        # 2. Revoke consent
        resp_rev = self.client.post(
            f"/api/v1/infrastructure/devices/{self.device_1.id}/consent/revoke/",
            {"reason": "Revocation for audit log test"},
            format="json",
            HTTP_X_WORKSPACE_ID=str(self.ws_1.id),
        )
        self.assertEqual(resp_rev.status_code, status.HTTP_200_OK)

        audit_revoke = LogEntry.objects.filter(
            object_pk=str(c1_id),
            action=LogEntry.Action.UPDATE,
        ).first()
        self.assertIsNotNone(audit_revoke)
        self.assertEqual(audit_revoke.actor, self.user_admin)
