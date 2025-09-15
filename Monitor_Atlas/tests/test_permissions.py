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
    """
    Tests that an EMASA user has permission to do an action on an object.

    In this case, the user is a member of the EMASA group, has a role that
    grants the get_by_id permission on the workspace, and the workspace is
    in the same region as the user.
    """
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
def test_emasa_user_has_permission_in_other_region():
    """
    Tests that an EMASA user has permission to do an action on an object
    in another region.

    In this case, the user is a member of the EMASA group, has a role that
    grants the put permission on the workspace, and the workspace is
    in the same region as the user.
    """
    reg = Region.objects.create(name="TestRegion")
    org = Organization.objects.create(name="EmasaOrg", region=reg)
    ws = Workspace.objects.create(name="TestWS", organization=org)
    role = Role.objects.create(name="AdminWS", workspace=ws)
    group = Group.objects.create(name="EMASA")
    user = User.objects.create_user(username="emasa_user", password="123")
    user.groups.add(group)
    WorkspaceMembership.objects.create(user=user, workspace=ws, role=role)

    org2 = Organization.objects.create(name="RandomOrg", region=reg)
    ws2 = Workspace.objects.create(name="RandomOrgWS", organization=org2)
    perm = PermissionKey.objects.create(
        scope="workspace",
        key_type="put",
        workspace=ws2,
    )
    role_permission = RolePermission.objects.create(role=role, permission_key=perm)
    assert has_permission(user, scope="workspace", action="put", obj=ws2)



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
    """
    Tests that an EMASA user can access a machine's detail view.

    The user is a member of the EMASA group and has a role that grants
    the get_by_id permission on the machine. The test verifies that the
    authenticated user's request to retrieve the machine's details
    returns a successful response.
    """

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

@pytest.mark.django_db
def test_machine_view_client_access():
    client = APIClient()
    reg = Region.objects.create(name="Colombia")
    org = Organization.objects.create(name="KFC", region=reg)
    ws = Workspace.objects.create(name="MainWS", organization=org)
    role = Role.objects.create(name="ViewerWS", workspace = ws)
    group = Group.objects.create(name="KFC-group")
    user = User.objects.create_user(username="client_user", password="123")
    user.groups.add(group)
    WorkspaceMembership.objects.create(user=user, workspace=ws, role=role)
    machine = Machine.objects.create(name="M1", workspace=ws)
    perm = PermissionKey.objects.create(
        scope="machine",
        key_type="get",
        machine=machine,
    )
    RolePermission.objects.create(role=role, permission_key=perm)
    client.force_authenticate(user=user)
    url = reverse("machine-detail", args=[machine.id])
    response = client.get(url)
    assert response.status_code == 200

@pytest.mark.django_db
def test_role_edit_role_client_success():
    client = APIClient()
    reg = Region.objects.create(name="Colombia")
    org = Organization.objects.create(name="KFC", region=reg)
    ws = Workspace.objects.create(name="MainWS", organization=org)
    role = Role.objects.create(name="Manager", workspace = ws, is_admin = True)
    group = Group.objects.create(name="KFC-group")
    user = User.objects.create_user(username="client_user", password="123")
    user.groups.add(group)
    WorkspaceMembership.objects.create(user=user, workspace=ws, role=role)

    new_role = Role.objects.create(name="Viewer", workspace = ws)

    perm = PermissionKey.objects.create(
        scope="role",
        key_type="put",
        role=new_role,
    )
    RolePermission.objects.create(role=role, permission_key=perm)

    client.force_authenticate(user=user)
    url = reverse("role-detail", args=[new_role.id])
    response = client.patch(url, {"name": "role_updated"}, format="json")

    assert response.status_code == 200
    new_role.refresh_from_db()
    assert new_role.name == "role_updated"

@pytest.mark.django_db
def test_role_edit_role_client_fail():
    client = APIClient()
    reg = Region.objects.create(name="Colombia")
    org = Organization.objects.create(name="KFC", region=reg)
    org2 = Organization.objects.create(name="KFC2", region=reg)
    ws = Workspace.objects.create(name="MainWS", organization=org)
    ws2 = Workspace.objects.create(name="MainWS2", organization=org2)
    role = Role.objects.create(name="Manager", workspace = ws, is_admin = True)
    role2 = Role.objects.create(name="Manager2", workspace = ws2, is_admin = True)
    group = Group.objects.create(name="KFC-group")
    group2 = Group.objects.create(name="KFC-group2")
    user = User.objects.create_user(username="client_user", password="123")
    user.groups.add(group)
    user2 = User.objects.create_user(username="client_user2", code="xd", password="123")
    user2.groups.add(group2)

    WorkspaceMembership.objects.create(user=user, workspace=ws, role=role)
    WorkspaceMembership.objects.create(user=user2, workspace=ws2, role=role2)

    new_role = Role.objects.create(name="Viewer", workspace = ws)

    perm = PermissionKey.objects.create(
        scope="role",
        key_type="put",
        role=new_role,
    )
    
    RolePermission.objects.create(role=role2, permission_key=perm)

    client.force_authenticate(user=user2)
    url = reverse("role-detail", args=[new_role.id])
    response = client.patch(url, {"name": "role_updated"}, format="json")

    assert response.status_code == 403

