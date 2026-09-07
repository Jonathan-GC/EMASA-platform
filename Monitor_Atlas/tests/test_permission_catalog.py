from django.test import TestCase
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework.exceptions import ValidationError

from organizations.models import Tenant, Workspace, Subscription
from roles.models import Role, WorkspaceMembership
from roles.catalog import PermissionCatalogRegistry, ResourceEntry
from roles.helpers import get_assignable_permissions, bulk_assign_permissions
from users.models import User
from infrastructure.models import Device, Gateway
from guardian.shortcuts import assign_perm


class PermissionCatalogRegistryTests(TestCase):
    def test_registry_categories_and_resources_structure(self):
        """Test registration, retrieval, and schema structure of PermissionCatalogRegistry."""
        categories = PermissionCatalogRegistry.get_categories()
        expected_categories = [
            "organizations",
            "infrastructure",
            "chirpstack",
            "roles",
            "users",
            "support",
        ]
        for cat_key in expected_categories:
            self.assertIn(cat_key, categories)
            cat = categories[cat_key]
            self.assertTrue(cat.label)
            self.assertTrue(cat.icon)
            self.assertTrue(len(cat.resources) > 0)

        # Check infrastructure resources
        infra = categories["infrastructure"]
        self.assertIn("device", infra.resources)
        self.assertIn("gateway", infra.resources)
        self.assertIn("application", infra.resources)
        self.assertIn("machine", infra.resources)
        self.assertIn("location", infra.resources)

        device_res = infra.resources["device"]
        self.assertEqual(device_res.app_label, "infrastructure")
        self.assertEqual(device_res.model, "device")
        self.assertIn("workspace", device_res.scopes)
        self.assertIn("view", device_res.actions)
        self.assertIn("change", device_res.actions)
        self.assertIn("delete", device_res.actions)

    def test_validate_registry_positive(self):
        """Test validate_registry succeeds on all pre-registered models."""
        self.assertTrue(PermissionCatalogRegistry.validate_registry())

    def test_validate_registry_catches_invalid_model(self):
        """Test validate_registry raises ValueError when an unregistered or invalid model is declared."""
        # Temporarily register an invalid resource
        invalid_res = ResourceEntry(
            app_label="infrastructure",
            model="nonexistentmodel123",
            label="Fake",
            icon="fake",
            scopes=["workspace"],
            actions=["view"],
        )
        cat = PermissionCatalogRegistry.get_categories()["infrastructure"]
        cat.resources["nonexistentmodel123"] = invalid_res

        try:
            with self.assertRaises(ValueError):
                PermissionCatalogRegistry.validate_registry()
        finally:
            # Clean up temporary resource
            del cat.resources["nonexistentmodel123"]


class PermissionCatalogAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.subscription = Subscription.objects.create(
            name="Catalog Test Sub",
            description="Catalog test subscription",
        )
        self.global_tenant = Tenant.objects.create(
            name="Global Master Tenant",
            subscription=self.subscription,
            is_global=True,
        )
        self.standard_tenant = Tenant.objects.create(
            name="Standard Tenant",
            subscription=self.subscription,
            is_global=False,
        )

        self.global_ws = Workspace.objects.create(
            name="Global Workspace", tenant=self.global_tenant
        )
        self.standard_ws = Workspace.objects.create(
            name="Standard Workspace", tenant=self.standard_tenant
        )

        # Users
        self.superuser = User.objects.create_superuser(
            username="super_catalog",
            email="super_cat@test.com",
            tenant=self.global_tenant,
        )
        self.standard_user = User.objects.create_user(
            username="std_catalog_user",
            email="std_cat@test.com",
            tenant=self.standard_tenant,
        )

    def test_catalog_unauthenticated_returns_401(self):
        """Unauthenticated requests to catalog endpoint must return HTTP 401."""
        response = self.client.get("/api/v1/roles/catalog/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response_direct = self.client.get("/api/v1/roles/role/catalog/")
        self.assertEqual(response_direct.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_catalog_authenticated_standard_tenant_filtering(self):
        """Standard tenant users receive only tenant/workspace scoped permissions and safe actions."""
        self.client.force_authenticate(user=self.standard_user)
        response = self.client.get("/api/v1/roles/catalog/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn("categories", data)

        categories = data["categories"]
        self.assertTrue(len(categories) > 0)

        # Verify safe actions (view, change) are returned for standard tenants
        for cat in categories:
            for res in cat["resources"]:
                self.assertIn("actions", res)
                self.assertEqual(set(res["actions"]), {"view", "change"})
                # Should not include delete for standard tenant
                self.assertNotIn("delete", res["actions"])

    def test_catalog_superuser_and_global_admin_receives_full_catalog(self):
        """Superusers and global admins receive full catalog with complete actions."""
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get("/api/v1/roles/catalog/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        categories = data["categories"]

        # Full actions should include view, change, delete
        for cat in categories:
            for res in cat["resources"]:
                self.assertIn("delete", res["actions"])


class AssignablePermissionsDynamicTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.subscription = Subscription.objects.create(name="Sub", description="Sub")
        self.tenant = Tenant.objects.create(
            name="Alpha Tenant", subscription=self.subscription, is_global=False
        )
        self.workspace = Workspace.objects.create(name="WS Alpha", tenant=self.tenant)

        # Role & user
        self.admin_group = Group.objects.create(name="admin_role_group")
        self.admin_role = Role.objects.create(
            name="Admin", workspace=self.workspace, group=self.admin_group, is_admin=True
        )
        self.admin_user = User.objects.create_user(
            username="ws_admin", email="admin@test.com", tenant=self.tenant
        )
        WorkspaceMembership.objects.create(
            user=self.admin_user, workspace=self.workspace, role=self.admin_role
        )
        # Give admin_user change_workspace to qualify as workspace admin
        assign_perm("change_workspace", self.admin_user, self.workspace)
        assign_perm("roles.change_role", self.admin_group)
        assign_perm("roles.view_role", self.admin_group)

        # Target role
        self.target_group = Group.objects.create(name="target_role_group")
        self.target_role = Role.objects.create(
            name="Operator", workspace=self.workspace, group=self.target_group
        )

        # Sin rol
        self.sin_rol = Role.objects.create(
            name="Sin rol", workspace=self.workspace
        )

        from infrastructure.models import Machine, Application

        self.machine = Machine.objects.create(name="Machine 1", workspace=self.workspace)
        self.application = Application.objects.create(name="App 1", workspace=self.workspace)

    def test_get_assignable_permissions_dynamic_objects(self):
        """get_assignable_permissions dynamically includes objects from catalog."""
        # Grant admin_group view_machine and change_machine on self.machine
        assign_perm("view_machine", self.admin_group, self.machine)
        assign_perm("change_machine", self.admin_group, self.machine)

        # Grant target_group view_machine on self.machine
        assign_perm("view_machine", self.target_group, self.machine)

        perms = get_assignable_permissions(self.admin_user, self.workspace, self.target_role)

        self.assertIn("object", perms)
        self.assertIn("machine", perms["object"])
        self.assertIn("application", perms["object"])

        # Check machine permissions evaluation
        machine_entries = perms["object"]["machine"]
        matching_machine = next((m for m in machine_entries if m["id"] == self.machine.id), None)
        self.assertIsNotNone(matching_machine)

        mach_perms = matching_machine["permissions"]
        self.assertTrue(mach_perms["view_machine"]["assigned"])
        self.assertTrue(mach_perms["view_machine"]["can_assign"])
        self.assertFalse(mach_perms["change_machine"]["assigned"])
        self.assertTrue(mach_perms["change_machine"]["can_assign"])

    def test_administrative_authority_bounding_can_assign(self):
        """Admin without change_machine cannot assign change_machine (can_assign is False)."""
        # Only assign view_machine to admin_group, omit change_machine
        assign_perm("view_machine", self.admin_group, self.machine)

        perms = get_assignable_permissions(self.admin_user, self.workspace, self.target_role)
        machine_entry = next(m for m in perms["object"]["machine"] if m["id"] == self.machine.id)

        self.assertTrue(machine_entry["permissions"]["view_machine"]["can_assign"])
        self.assertFalse(machine_entry["permissions"]["change_machine"]["can_assign"])

    def test_sin_rol_protection(self):
        """Sin rol role returns empty assignable permissions and rejects bulk assignment."""
        perms = get_assignable_permissions(self.admin_user, self.workspace, self.sin_rol)
        self.assertEqual(perms, {"global": {}, "object": {}})

        # Directly invoking bulk_assign_permissions on Sin rol raises ValidationError
        with self.assertRaises(ValidationError):
            bulk_assign_permissions({"assign": {"machine": {"view_machine": [self.machine.id]}}}, self.sin_rol)

        # Calling viewset action on Sin rol returns 400 Bad Request
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.patch(
            f"/api/v1/roles/role/{self.sin_rol.id}/bulk_assign_permissions/",
            {"permissions": {"assign": {"machine": {"view_machine": [self.machine.id]}}}},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
