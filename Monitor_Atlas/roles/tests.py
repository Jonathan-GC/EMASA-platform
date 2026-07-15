from django.test import TestCase

from rest_framework.test import APIClient

from organizations.models import Subscription, Tenant, Workspace
from roles.models import Role, WorkspaceMembership
from users.models import User


class RoleRemoveUserActionTests(TestCase):

    def setUp(self):
        self.client = APIClient()

        subscription = Subscription.objects.create(
            name="sub",
            description="sub",
            can_have_gateways=False,
            max_device_count=0,
            max_gateway_count=0,
        )
        tenant = Tenant.objects.create(name="tenant", subscription=subscription)
        self.workspace = Workspace.objects.create(
            name="ws",
            description="ws",
            tenant=tenant,
        )

        self.admin = User.objects.create_superuser(
            username="admin",
            password="password",
            name="Admin",
            last_name="User",
            email="admin@example.com",
            phone="123",
            tenant=tenant,
        )
        self.client.force_authenticate(user=self.admin)

        self.user = User.objects.create_user(
            username="member",
            password="password",
            name="Member",
            last_name="User",
            email="member@example.com",
            phone="456",
            tenant=tenant,
        )

        self.role = Role.objects.create(
            name="Operator",
            description="role",
            workspace=self.workspace,
        )
        self.membership = WorkspaceMembership.objects.create(
            workspace=self.workspace,
            user=self.user,
            role=self.role,
        )

    def test_remove_user_requires_user_id(self):
        url = f"/api/v1/roles/role/{self.role.id}/remove_user/"
        res = self.client.post(url, data={}, format="json")
        self.assertEqual(res.status_code, 400)
        self.assertIn("detail", res.data)

    def test_remove_user_deletes_membership_and_group(self):
        self.assertTrue(
            WorkspaceMembership.objects.filter(pk=self.membership.pk).exists()
        )
        self.assertTrue(self.user.groups.filter(pk=self.role.group.pk).exists())

        url = f"/api/v1/roles/role/{self.role.id}/remove_user/"
        res = self.client.post(url, data={"user_id": self.user.id}, format="json")
        self.assertEqual(res.status_code, 200)

        self.assertFalse(
            WorkspaceMembership.objects.filter(pk=self.membership.pk).exists()
        )
        self.assertFalse(self.user.groups.filter(pk=self.role.group.pk).exists())
