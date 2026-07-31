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

    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get("/api/v1/users/user/profile/")
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
