"""Tests for the Google OAuth2 callback flow.

The login endpoint exchanges an authorization ``code`` for an ID token and only
signs in users that already have a linked ``OAuthAccount``.
"""
from unittest.mock import Mock

import pytest
from django.urls import reverse
from google.oauth2 import id_token
from rest_framework.test import APIClient

from users.models import OAuthAccount, User


def _token_exchange_response(payload):
    response = Mock()
    response.raise_for_status = Mock()
    response.json.return_value = payload
    return response


def _valid_idinfo(**overrides):
    idinfo = {
        "aud": "test-client-id",
        "iss": "https://accounts.google.com",
        "email": "user@example.com",
        "sub": "1234567890",
    }
    idinfo.update(overrides)
    return idinfo


@pytest.fixture
def linked_user(db):
    user = User.objects.create_user(
        username="google_user", email="user@example.com"
    )
    OAuthAccount.objects.create(
        user=user,
        provider="google",
        provider_user_id="1234567890",
        email="user@example.com",
    )
    return user


@pytest.mark.django_db
def test_google_login_valid_token(monkeypatch, settings, linked_user):
    client = APIClient()
    settings.GOOGLE_CLIENT_ID = "test-client-id"
    settings.GOOGLE_ISS = "https://accounts.google.com"

    monkeypatch.setattr(
        "users.views.http_requests.post",
        lambda *args, **kwargs: _token_exchange_response(
            {"id_token": "fake-id-token"}
        ),
    )
    monkeypatch.setattr(id_token, "verify_oauth2_token", lambda token, req: _valid_idinfo())

    response = client.post(
        reverse("google-callback"),
        {"code": "fake-code"},
        format="json",
    )

    assert response.status_code == 200
    assert "access" in response.data
    assert settings.REFRESH_COOKIE_NAME in response.cookies


@pytest.mark.django_db
def test_google_login_invalid_aud(monkeypatch, settings):
    client = APIClient()
    settings.GOOGLE_CLIENT_ID = "expected-client-id"
    settings.GOOGLE_ISS = "https://accounts.google.com"

    monkeypatch.setattr(
        "users.views.http_requests.post",
        lambda *args, **kwargs: _token_exchange_response(
            {"id_token": "fake-id-token"}
        ),
    )
    monkeypatch.setattr(
        id_token,
        "verify_oauth2_token",
        lambda token, req: _valid_idinfo(aud="other-client-id"),
    )

    response = client.post(
        reverse("google-callback"), {"code": "fake-code"}, format="json"
    )
    assert response.status_code == 401
    assert response.data["detail"] == "Invalid audience."


@pytest.mark.django_db
def test_google_login_invalid_iss(monkeypatch, settings):
    """Returns 401 when the token issuer (iss) is not allowed."""
    client = APIClient()
    settings.GOOGLE_CLIENT_ID = "test-client-id"
    settings.GOOGLE_ISS = "https://accounts.google.com"

    monkeypatch.setattr(
        "users.views.http_requests.post",
        lambda *args, **kwargs: _token_exchange_response(
            {"id_token": "fake-id-token"}
        ),
    )
    monkeypatch.setattr(
        id_token,
        "verify_oauth2_token",
        lambda token, req: _valid_idinfo(iss="https://malicious.com"),
    )

    response = client.post(
        reverse("google-callback"), {"code": "fake-code"}, format="json"
    )
    assert response.status_code == 401
    assert response.data["detail"] == "Invalid issuer."


@pytest.mark.django_db
def test_google_login_missing_sub(monkeypatch, settings):
    """Returns 400 when the verified token is missing the subject field."""
    client = APIClient()
    settings.GOOGLE_CLIENT_ID = "test-client-id"
    settings.GOOGLE_ISS = "https://accounts.google.com"

    idinfo = _valid_idinfo()
    idinfo.pop("sub")

    monkeypatch.setattr(
        "users.views.http_requests.post",
        lambda *args, **kwargs: _token_exchange_response(
            {"id_token": "fake-id-token"}
        ),
    )
    monkeypatch.setattr(
        id_token, "verify_oauth2_token", lambda token, req: idinfo
    )

    response = client.post(
        reverse("google-callback"), {"code": "fake-code"}, format="json"
    )
    assert response.status_code == 400
    assert response.data["detail"] == "Invalid token payload."


@pytest.mark.django_db
def test_google_login_verify_raises_valueerror(monkeypatch, settings):
    """Returns 401 when verify_oauth2_token raises ValueError (invalid token)."""
    client = APIClient()
    settings.GOOGLE_CLIENT_ID = "test-client-id"
    settings.GOOGLE_ISS = "https://accounts.google.com"

    monkeypatch.setattr(
        "users.views.http_requests.post",
        lambda *args, **kwargs: _token_exchange_response(
            {"id_token": "fake-id-token"}
        ),
    )

    def raise_value_error(token, req):
        raise ValueError("Invalid token")

    monkeypatch.setattr(id_token, "verify_oauth2_token", raise_value_error)

    response = client.post(
        reverse("google-callback"), {"code": "fake-code"}, format="json"
    )
    assert response.status_code == 401
    assert "Invalid token" in response.data.get("detail", "")


@pytest.mark.django_db
def test_google_login_missing_code(settings):
    """Returns 400 when the authorization code is missing."""
    client = APIClient()
    settings.GOOGLE_CLIENT_ID = "test-client-id"

    response = client.post(reverse("google-callback"), {}, format="json")

    assert response.status_code == 400
    assert response.data["detail"] == "Authorization code is required."


@pytest.mark.django_db
def test_google_login_unlinked_identity(monkeypatch, settings):
    """Returns 404 when no OAuthAccount is linked to the Google identity."""
    client = APIClient()
    settings.GOOGLE_CLIENT_ID = "test-client-id"
    settings.GOOGLE_ISS = "https://accounts.google.com"

    monkeypatch.setattr(
        "users.views.http_requests.post",
        lambda *args, **kwargs: _token_exchange_response(
            {"id_token": "fake-id-token"}
        ),
    )
    monkeypatch.setattr(
        id_token,
        "verify_oauth2_token",
        lambda token, req: _valid_idinfo(sub="not-linked"),
    )

    response = client.post(
        reverse("google-callback"), {"code": "fake-code"}, format="json"
    )
    assert response.status_code == 404
    assert response.data["code"] == "no_linked_account"
    assert response.data["email"] == "user@example.com"
