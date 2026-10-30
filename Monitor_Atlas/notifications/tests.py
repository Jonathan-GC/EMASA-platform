import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from organizations.models import Tenant, Subscription
from notifications.models import FCMDevice

User = get_user_model()


@pytest.mark.django_db
def test_fcm_device_registration_ownership_transfer():
    subscription = Subscription.objects.create(name="Pro", description="Pro plan")
    tenant = Tenant.objects.create(name="FCM Corp", subscription=subscription)

    user1 = User.objects.create_user(
        username="fcm_user_1",
        email="u1@fcm.com",
        password="Password123!",
        tenant=tenant,
    )
    user2 = User.objects.create_user(
        username="fcm_user_2",
        email="u2@fcm.com",
        password="Password123!",
        tenant=tenant,
    )

    client = APIClient()

    # User 1 registers device on PC 1
    client.force_authenticate(user=user1)
    res1 = client.post(
        "/api/v1/notifications/devices/register/",
        {"fcm_token": "pc1_shared_token_abc123", "platform": "web"},
        format="json",
    )
    assert res1.status_code in [200, 201], f"User 1 registration failed: {res1.data}"
    device = FCMDevice.objects.get(fcm_token="pc1_shared_token_abc123")
    assert device.user == user1
    assert device.is_active is True

    # User 2 logs into the same PC 1 and registers the same token
    client.force_authenticate(user=user2)
    res2 = client.post(
        "/api/v1/notifications/devices/register/",
        {"fcm_token": "pc1_shared_token_abc123", "platform": "web"},
        format="json",
    )
    assert res2.status_code in [200, 201], f"User 2 registration failed with: {res2.data}"

    device.refresh_from_db()
    assert device.user == user2, "Device ownership should have transferred to User 2"
    assert device.is_active is True


@pytest.mark.django_db
def test_logout_deactivates_fcm_device():
    subscription = Subscription.objects.create(name="Pro", description="Pro plan")
    tenant = Tenant.objects.create(name="Logout Corp", subscription=subscription)

    user = User.objects.create_user(
        username="logout_user",
        email="u@logout.com",
        password="Password123!",
        tenant=tenant,
    )

    device = FCMDevice.objects.create(
        user=user,
        fcm_token="token_to_logout_deactivate",
        platform="web",
        is_active=True,
    )

    client = APIClient()
    client.force_authenticate(user=user)

    res = client.post(
        "/api/v1/logout/",
        {"fcm_token": "token_to_logout_deactivate"},
        format="json",
    )
    assert res.status_code == 204

    device.refresh_from_db()
    assert device.is_active is False, "FCMDevice should be marked is_active=False on logout"
