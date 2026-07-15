import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from google.oauth2 import id_token


@pytest.mark.django_db
def test_google_login_valid_token(monkeypatch, settings):
    client = APIClient()
    settings.GOOGLE_CLIENT_ID = "test-client-id"
    settings.GOOGLE_ISS = "https://accounts.google.com"

    # Mock de verify_oauth2_token
    def mock_verify(token, req):
        return {
            "aud": "test-client-id",
            "iss": "https://accounts.google.com",
            "email": "user@example.com",
            "sub": "1234567890",
        }

    monkeypatch.setattr(id_token, "verify_oauth2_token", mock_verify)

    response = client.post(
        reverse("google-login"),
        {"id_token": "fake-token"},
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

    def mock_verify(token, req):
        return {
            "aud": "other-client-id",  # aud incorrecto
            "iss": "https://accounts.google.com",
            "email": "user@example.com",
            "sub": "1234567890",
        }

    monkeypatch.setattr(id_token, "verify_oauth2_token", mock_verify)

    response = client.post(
        reverse("google-login"), {"id_token": "fake-token"}, format="json"
    )
    assert response.status_code == 401
    assert response.data["detail"] == "Invalid audience."


@pytest.mark.django_db
def test_google_login_invalid_iss(monkeypatch, settings):
    """Returns 401 when the token issuer (iss) is not allowed."""
    client = APIClient()
    settings.GOOGLE_CLIENT_ID = "test-client-id"
    settings.GOOGLE_ISS = "https://accounts.google.com"

    def mock_verify(token, req):
        return {
            "aud": "test-client-id",
            "iss": "https://malicious.com",
            "email": "user@example.com",
            "sub": "1234567890",
        }

    monkeypatch.setattr(id_token, "verify_oauth2_token", mock_verify)

    response = client.post(
        reverse("google-login"), {"id_token": "fake-token"}, format="json"
    )
    assert response.status_code == 401
    assert response.data["detail"] == "Invalid issuer."


@pytest.mark.django_db
def test_google_login_missing_email(monkeypatch, settings):
    """Returns 400 when the verified token is missing the email field."""
    client = APIClient()
    settings.GOOGLE_CLIENT_ID = "test-client-id"
    settings.GOOGLE_ISS = "https://accounts.google.com"

    def mock_verify(token, req):
        return {
            "aud": "test-client-id",
            "iss": "https://accounts.google.com",
            # email missing
            "sub": "1234567890",
        }

    monkeypatch.setattr(id_token, "verify_oauth2_token", mock_verify)

    response = client.post(
        reverse("google-login"), {"id_token": "fake-token"}, format="json"
    )
    assert response.status_code == 400
    assert response.data["detail"] == "Invalid token payload."


@pytest.mark.django_db
def test_google_login_verify_raises_valueerror(monkeypatch, settings):
    """Returns 401 when verify_oauth2_token raises ValueError (invalid token)."""
    client = APIClient()
    settings.GOOGLE_CLIENT_ID = "test-client-id"
    settings.GOOGLE_ISS = "https://accounts.google.com"

    def mock_verify(token, req):
        raise ValueError("Invalid token")

    monkeypatch.setattr(id_token, "verify_oauth2_token", mock_verify)

    response = client.post(
        reverse("google-login"), {"id_token": "fake-token"}, format="json"
    )
    assert response.status_code == 401
    # message comes from the exception in the view
    assert "Invalid token" in response.data.get("detail", "")
