import pytest
from rest_framework.test import APIClient
from users.models import User, OAuthAccount, MainAddress
from organizations.models import Tenant, Subscription, Workspace
from roles.models import Role, WorkspaceMembership


@pytest.mark.django_db
def test_user_me_endpoint_google_oauth_unlinked():
    user = User.objects.create_user(
        username="testmeuser",
        email="testmeuser@example.com",
        password="Password123!",
        name="Test",
        last_name="User",
    )
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get("/api/v1/users/user/me/")
    assert response.status_code == 200
    data = response.data
    assert "google_oauth" in data
    assert data["google_oauth"]["is_linked"] is False
    assert data["google_oauth"]["email"] is None


@pytest.mark.django_db
def test_user_me_endpoint_google_oauth_linked():
    subscription = Subscription.objects.create(name="Basic", description="Basic plan")
    tenant = Tenant.objects.create(name="Acme Corp", description="Acme Tenant", subscription=subscription)
    user = User.objects.create_user(
        username="testmeuser2",
        email="testmeuser2@example.com",
        password="Password123!",
        name="Test",
        last_name="User",
        tenant=tenant,
    )
    workspace = Workspace.objects.create(
        name="Default Workspace", description="Main workspace", tenant=tenant
    )
    role = Role.objects.create(
        name="Admin", description="Admin role", color="#FF0000", workspace=workspace
    )
    WorkspaceMembership.objects.create(user=user, workspace=workspace, role=role)

    OAuthAccount.objects.create(
        user=user,
        provider="google",
        provider_user_id="google-sub-12345",
        email="googleuser@example.com",
    )
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get("/api/v1/users/user/me/")
    assert response.status_code == 200
    data = response.data
    assert "google_oauth" in data
    assert data["google_oauth"]["is_linked"] is True
    assert data["google_oauth"]["email"] == "googleuser@example.com"
    assert data["google_oauth"]["provider_user_id"] == "google-sub-12345"

    assert "tenant" in data
    assert data["tenant"]["id"] == tenant.id
    assert data["tenant"]["name"] == "Acme Corp"
    assert data["tenant"]["description"] == "Acme Tenant"

    assert "roles" in data
    assert len(data["roles"]) == 1
    assert data["roles"][0]["name"] == "Admin"
    assert data["roles"][0]["workspace"]["name"] == "Default Workspace"


@pytest.mark.django_db
def test_user_profile_endpoint():
    subscription = Subscription.objects.create(name="Basic", description="Basic plan")
    tenant = Tenant.objects.create(name="Acme Corp", subscription=subscription)
    address = MainAddress.objects.create(
        address="123 Main St", city="City", state="State", zip_code="12345"
    )
    user = User.objects.create_user(
        username="profileuser",
        email="profileuser@example.com",
        password="Password123!",
        name="John",
        last_name="Doe",
        phone="1234567890",
        phone_code="+1",
        country="USA",
        tenant=tenant,
        address=address,
    )
    workspace = Workspace.objects.create(
        name="Default Workspace", description="Main workspace", tenant=tenant
    )
    role = Role.objects.create(
        name="Engineer", description="Dev role", color="#00FF00", workspace=workspace
    )
    WorkspaceMembership.objects.create(user=user, workspace=workspace, role=role)

    superuser = User.objects.create_superuser(
        username="adminuser",
        email="adminuser@example.com",
        password="Password123!",
    )
    client = APIClient()
    client.force_authenticate(user=superuser)

    response = client.get(f"/api/v1/users/user/{user.id}/profile/")
    assert response.status_code == 200
    data = response.data

    # Check required top-level keys
    assert "roles" in data
    assert "user_info" in data
    assert "status" in data
    assert "tenant" in data
    assert "contact_info" in data

    # Check user_info structure
    assert data["user_info"]["username"] == "profileuser"
    assert data["user_info"]["email"] == "profileuser@example.com"
    assert data["user_info"]["full_name"] == "John Doe"

    # Check status structure
    assert data["status"]["is_active"] is True
    assert data["status"]["status_text"] == "Active"

    # Check tenant structure
    assert data["tenant"]["id"] == tenant.id
    assert data["tenant"]["name"] == "Acme Corp"

    # Check contact_info structure
    assert data["contact_info"]["email"] == "profileuser@example.com"
    assert data["contact_info"]["phone"] == "1234567890"
    assert data["contact_info"]["address"]["address"] == "123 Main St"

    # Check roles structure
    assert len(data["roles"]) == 1
    assert data["roles"][0]["name"] == "Engineer"
    assert data["roles"][0]["workspace"]["name"] == "Default Workspace"


@pytest.mark.django_db
def test_google_unlink_success():
    user = User.objects.create_user(
        username="unlinkuser",
        email="unlinkuser@example.com",
        password="Password123!",
        name="Unlink",
        last_name="User",
    )
    OAuthAccount.objects.create(
        user=user,
        provider="google",
        provider_user_id="google-sub-99999",
        email="unlinkuser@example.com",
    )
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.post("/api/v1/users/auth/google/unlink/")
    assert response.status_code == 200
    assert response.data["detail"] == "Google account unlinked successfully."
    assert not OAuthAccount.objects.filter(user=user, provider="google").exists()


@pytest.mark.django_db
def test_google_unlink_not_linked():
    user = User.objects.create_user(
        username="nounlinkuser",
        email="nounlinkuser@example.com",
        password="Password123!",
        name="NoUnlink",
        last_name="User",
    )
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.post("/api/v1/users/auth/google/unlink/")
    assert response.status_code == 400
    assert response.data["detail"] == "No Google account linked to this user."


@pytest.mark.django_db
def test_tenant_owner_can_view_employee_profile_and_other_employee_cannot():
    from guardian.shortcuts import assign_perm
    from roles.helpers import assign_new_tenant_base_permissions, assign_new_user_base_permissions

    subscription = Subscription.objects.create(name="Pro", description="Pro plan")
    tenant = Tenant.objects.create(name="Beta Corp", subscription=subscription)

    owner = User.objects.create_user(
        username="owner_user",
        email="owner@betacorp.com",
        password="Password123!",
        name="Owner",
        last_name="Boss",
        tenant=tenant,
    )
    assign_new_tenant_base_permissions(tenant, owner)

    employee = User.objects.create_user(
        username="emp_user",
        email="emp@betacorp.com",
        password="Password123!",
        name="Employee",
        last_name="Worker",
        tenant=tenant,
    )
    assign_new_user_base_permissions(employee)

    other_employee = User.objects.create_user(
        username="other_emp_user",
        email="other@betacorp.com",
        password="Password123!",
        name="Other",
        last_name="Worker",
        tenant=tenant,
    )
    assign_new_user_base_permissions(other_employee)

    # 1. Tenant owner views employee profile
    client = APIClient()
    client.force_authenticate(user=owner)
    res = client.get(f"/api/v1/users/user/{employee.id}/profile/")
    assert res.status_code == 200, f"Expected 200 for tenant owner viewing employee profile, got {res.status_code}: {res.data}"
    assert res.data["user_info"]["username"] == "emp_user"

    # 2. Employee views own profile
    client.force_authenticate(user=employee)
    res_self = client.get(f"/api/v1/users/user/{employee.id}/profile/")
    assert res_self.status_code == 200

    # 3. Employee views peer employee profile -> 403 Forbidden
    res_peer = client.get(f"/api/v1/users/user/{other_employee.id}/profile/")
    assert res_peer.status_code == 403, f"Expected 403 for peer employee viewing another profile, got {res_peer.status_code}"


@pytest.mark.django_db
def test_profile_audit_endpoint():
    from guardian.shortcuts import assign_perm
    from auditlog.models import LogEntry
    from django.contrib.contenttypes.models import ContentType
    from roles.helpers import assign_new_tenant_base_permissions, assign_new_user_base_permissions

    subscription = Subscription.objects.create(name="Pro", description="Pro plan")
    tenant = Tenant.objects.create(name="Gamma Corp", subscription=subscription)

    owner = User.objects.create_user(
        username="gamma_owner",
        email="owner@gamma.com",
        password="Password123!",
        tenant=tenant,
    )
    assign_new_tenant_base_permissions(tenant, owner)

    emp = User.objects.create_user(
        username="gamma_emp",
        email="emp@gamma.com",
        password="Password123!",
        tenant=tenant,
    )
    assign_new_user_base_permissions(emp)

    peer = User.objects.create_user(
        username="gamma_peer",
        email="peer@gamma.com",
        password="Password123!",
        tenant=tenant,
    )
    assign_new_user_base_permissions(peer)

    superuser = User.objects.create_superuser(
        username="gamma_super",
        email="super@gamma.com",
        password="Password123!",
    )

    # Create dummy audit log for emp
    user_ct = ContentType.objects.get_for_model(User)
    LogEntry.objects.create(
        content_type=user_ct,
        object_pk=str(emp.id),
        object_repr=str(emp),
        action=LogEntry.Action.UPDATE,
        actor=emp,
        changes='{"name": ["old", "new"]}',
    )

    client = APIClient()

    # 1. Emp views own profile audit
    client.force_authenticate(user=emp)
    res_self = client.get(f"/api/v1/users/user/{emp.id}/profile_audit/")
    assert res_self.status_code == 200, f"Expected 200 for self profile_audit, got {res_self.status_code}"
    results = res_self.data.get("results", res_self.data)
    assert len(results) >= 1

    # 2. Owner views emp's profile audit
    client.force_authenticate(user=owner)
    res_owner = client.get(f"/api/v1/users/user/{emp.id}/profile_audit/")
    assert res_owner.status_code == 200, f"Expected 200 for owner profile_audit, got {res_owner.status_code}"

    # 3. Superuser views emp's profile audit
    client.force_authenticate(user=superuser)
    res_super = client.get(f"/api/v1/users/user/{emp.id}/profile_audit/")
    assert res_super.status_code == 200

    # 4. Peer employee views emp's profile audit -> 403 Forbidden
    client.force_authenticate(user=peer)
    res_peer = client.get(f"/api/v1/users/user/{emp.id}/profile_audit/")
    assert res_peer.status_code == 403


