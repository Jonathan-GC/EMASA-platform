import pytest
from django.contrib.auth.models import Group
from organizations.models import Organization, Workspace, Region
from users.models import User
from roles.models import PermissionKey, Role, WorkspaceMembership, RolePermission
from roles.permissions import has_permission
from infrastructure.models import Machine
from rest_framework.test import APIClient
from django.urls import reverse

@pytest.mark.django_db
def test_emasa_user_has_permission():
    reg = Region.objects.create(name="TestRegion")
    org = Organization.objects.create(name="EmasaOrg", region=reg)
    ws = Workspace.objects.create(name="TestWS", organization=org)
    role = Role.objects.create(name="AdminWS", workspace=ws)
    group = Group.objects.create(name="EMASA")
    user = User.objects.create_user(username="emasa_user", password="123")
    user.groups.add(group)
    WorkspaceMembership.objects.create(user=user, workspace=ws, role=role)
    perm = PermissionKey.objects.create(
        scope="workspace",
        key_type="get_by_id",
        workspace=ws,
    )
    role_permission = RolePermission.objects.create(role=role, permission_key=perm)
    assert has_permission(user, scope="workspace", action="get_by_id", obj=ws)

@pytest.mark.django_db
def test_normal_user_without_permission_fails():
    reg = Region.objects.create(name="TestRegion")
    org = Organization.objects.create(name="ClientOrg", region=reg)
    ws = Workspace.objects.create(name="ClientWS", organization=org)
    role = Role.objects.create(name="ViewerWS", workspace=ws)
    user = User.objects.create_user(username="client_user", password="123")
    WorkspaceMembership.objects.create(user=user, workspace=ws, role=role)
    assert has_permission(user, scope="workspace", action="get", obj=ws) is False

@pytest.mark.django_db
def test_machine_view_emasa_access():
    client = APIClient()
    reg = Region.objects.create(name="TestRegion")
    org = Organization.objects.create(name="EmasaOrg", region=reg)
    ws = Workspace.objects.create(name="TestWS", organization=org)
    role = Role.objects.create(name="AdminWS", workspace = ws)
    group = Group.objects.create(name="EMASA")
    user = User.objects.create_user(username="emasa_user", password="123")
    user.groups.add(group)
    WorkspaceMembership.objects.create(user=user, workspace=ws, role=role)
    machine = Machine.objects.create(name="M1", workspace=ws)
    perm = PermissionKey.objects.create(
        scope="machine",
        key_type="get_by_id",
        machine=machine,
    )
    RolePermission.objects.create(role=role, permission_key=perm)
    client.force_authenticate(user=user)
    url = reverse("machine-detail", args=[machine.id])
    response = client.get(url)
    assert response.status_code == 200
