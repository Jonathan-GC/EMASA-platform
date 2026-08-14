import os
import requests
from unittest.mock import patch, MagicMock
from django.test import TestCase, SimpleTestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
import botocore.exceptions

from system.health import (
    check_database_health,
    check_r2_storage_health,
    check_mailgun_health,
    check_chirpstack_health,
    check_firebase_health,
    check_hermes_health,
    get_atlas_services_health,
    get_system_health_report,
)


class AppsModelsEndpointTests(SimpleTestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("system-apps")
        self.models_url = reverse("system-models")

    def test_get_apps_models_default_returns_platform_apps(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertIn("apps", data)
        self.assertIn("models_by_app", data)
        self.assertIn("all_models", data)
        self.assertIn("total_apps", data)
        self.assertIn("total_models", data)

        app_labels = [app["app_label"] for app in data["apps"]]
        # Core platform apps must be included
        expected_apps = ["users", "roles", "organizations", "infrastructure", "chirpstack", "support", "notifications"]
        for expected in expected_apps:
            self.assertIn(expected, app_labels)
            self.assertIn(expected, data["models_by_app"])

        # Built-in apps like 'sessions' or 'contenttypes' should not be in default
        self.assertNotIn("sessions", app_labels)
        self.assertNotIn("contenttypes", app_labels)

        # Check model structure inside an app (e.g. users)
        users_app = next(a for a in data["apps"] if a["app_label"] == "users")
        user_model = next((m for m in users_app["models"] if m["object_name"] == "User"), None)
        self.assertIsNotNone(user_model)
        self.assertEqual(user_model["model_name"], "user")
        self.assertEqual(user_model["app_label"], "users")
        self.assertTrue(len(user_model["db_table"]) > 0)

    def test_get_apps_models_include_all_true(self):
        response = self.client.get(self.url, {"include_all": "true"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        app_labels = [app["app_label"] for app in data["apps"]]
        self.assertIn("auth", app_labels)
        self.assertIn("contenttypes", app_labels)
        self.assertIn("sessions", app_labels)
        self.assertIn("users", app_labels)

    def test_get_apps_models_filter_by_app(self):
        response = self.client.get(self.url, {"app": "infrastructure"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertEqual(data["total_apps"], 1)
        self.assertEqual(data["apps"][0]["app_label"], "infrastructure")
        model_names = [m["object_name"] for m in data["apps"][0]["models"]]
        self.assertIn("Device", model_names)
        self.assertIn("Gateway", model_names)
        self.assertIn("Measurements", model_names)

    def test_models_url_alias(self):
        response = self.client.get(self.models_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn("apps", data)
        self.assertIn("models_by_app", data)


class SystemHealthUnitTests(SimpleTestCase):
    allow_database_queries = True

    def test_check_database_health_success(self):
        with patch("system.health.connection") as mock_conn:
            cursor_mock = MagicMock()
            mock_conn.cursor.return_value.__enter__.return_value = cursor_mock
            cursor_mock.fetchone.return_value = (1,)

            result = check_database_health()
            self.assertEqual(result["status"], "healthy")
            self.assertIn("latency_ms", result)

    def test_check_database_health_failure(self):
        with patch("system.health.connection") as mock_conn:
            mock_conn.cursor.side_effect = Exception("DB Connection Error")

            result = check_database_health()
            self.assertEqual(result["status"], "unhealthy")
            self.assertIn("error", result)

    @override_settings(USE_R2=False, MEDIA_ROOT="/tmp/test_media_health")
    def test_check_r2_storage_health_disabled(self):
        result = check_r2_storage_health()
        self.assertFalse(result["enabled"])
        self.assertEqual(result["backend"], "filesystem")
        self.assertIn(result["status"], ("healthy", "degraded"))

    @override_settings(
        USE_R2=True,
        R2_BUCKET_NAME="my-bucket",
        R2_ENDPOINT_URL="https://account.r2.cloudflarestorage.com",
        R2_ACCESS_KEY_ID="test_access_key",
        R2_SECRET_ACCESS_KEY="test_secret_key",
        R2_CUSTOM_DOMAIN="https://pub-cdn.dev",
        R2_REGION_NAME="auto",
    )
    @patch("boto3.client")
    def test_check_r2_storage_health_enabled_success(self, mock_boto_client):
        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3

        result = check_r2_storage_health()
        self.assertTrue(result["enabled"])
        self.assertEqual(result["status"], "healthy")
        self.assertEqual(result["bucket"], "my-bucket")
        self.assertEqual(result["custom_domain"], "https://pub-cdn.dev")
        mock_s3.head_bucket.assert_called_once_with(Bucket="my-bucket")

    @override_settings(
        USE_R2=True,
        R2_BUCKET_NAME="my-bucket",
        R2_ENDPOINT_URL="https://account.r2.cloudflarestorage.com",
        R2_ACCESS_KEY_ID="test_access_key",
        R2_SECRET_ACCESS_KEY="test_secret_key",
    )
    @patch("boto3.client")
    def test_check_r2_storage_health_enabled_failure(self, mock_boto_client):
        mock_s3 = MagicMock()
        mock_s3.head_bucket.side_effect = botocore.exceptions.ClientError(
            {"Error": {"Code": "404", "Message": "Not Found"}}, "head_bucket"
        )
        mock_boto_client.return_value = mock_s3

        result = check_r2_storage_health()
        self.assertTrue(result["enabled"])
        self.assertEqual(result["status"], "unhealthy")
        self.assertIn("error", result)

    @override_settings(
        MAILGUN_API_KEY="key-123456",
        MAILGUN_DOMAIN="mg.example.com",
    )
    @patch("requests.get")
    def test_check_mailgun_health_success(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"domain": {"name": "mg.example.com", "state": "active"}}
        mock_get.return_value = mock_resp

        result = check_mailgun_health()
        self.assertTrue(result["configured"])
        self.assertEqual(result["status"], "healthy")
        self.assertEqual(result["domain"], "mg.example.com")
        self.assertEqual(result["domain_state"], "active")
        mock_get.assert_called_once_with(
            "https://api.mailgun.net/v3/domains/mg.example.com",
            auth=("api", "key-123456"),
            timeout=5,
        )

    @override_settings(
        MAILGUN_API_KEY="key-invalid",
        MAILGUN_DOMAIN="mg.example.com",
    )
    @patch("requests.get")
    def test_check_mailgun_health_unauthorized(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_get.return_value = mock_resp

        result = check_mailgun_health()
        self.assertTrue(result["configured"])
        self.assertEqual(result["status"], "unhealthy")
        self.assertIn("error", result)

    @override_settings(MAILGUN_API_KEY=None, MAILGUN_DOMAIN=None)
    def test_check_mailgun_health_not_configured(self):
        result = check_mailgun_health()
        self.assertFalse(result["configured"])
        self.assertEqual(result["status"], "not_configured")

    @override_settings(
        CHIRPSTACK_BASE_URL="http://localhost:8090/api",
        CHIRPSTACK_JWT_TOKEN="jwt.token.test",
    )
    @patch("requests.get")
    def test_check_chirpstack_health_success(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_get.return_value = mock_resp

        result = check_chirpstack_health()
        self.assertTrue(result["configured"])
        self.assertEqual(result["status"], "healthy")

    @override_settings(CHIRPSTACK_BASE_URL=None, CHIRPSTACK_JWT_TOKEN=None)
    def test_check_chirpstack_health_not_configured(self):
        result = check_chirpstack_health()
        self.assertFalse(result["configured"])
        self.assertEqual(result["status"], "not_configured")

    @override_settings(
        HERMES_API_URL="http://localhost:5000",
        HERMES_WS_URL="ws://localhost:5000",
        SERVICE_API_KEY="secret_service_key",
    )
    @patch("requests.get")
    def test_check_hermes_health_success(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {"content-type": "application/json"}
        mock_resp.json.return_value = {
            "status": "healthy",
            "service": "Monitor_Hermes",
            "components": {
                "database": {"status": "healthy"},
                "redis": {"status": "healthy"},
                "websockets": {"status": "healthy", "total_connections": 5},
                "mqtt": {"status": "connected"},
            },
        }
        mock_get.return_value = mock_resp

        result = check_hermes_health()
        self.assertTrue(result["configured"])
        self.assertEqual(result["status"], "healthy")
        self.assertEqual(result["api_url"], "http://localhost:5000")
        self.assertEqual(result["ws_url"], "ws://localhost:5000")
        self.assertEqual(result["details"]["components"]["websockets"]["total_connections"], 5)
        mock_get.assert_called_once_with(
            "http://localhost:5000/health",
            headers={"X-API-Key": "secret_service_key"},
            timeout=5,
        )

    @override_settings(
        HERMES_API_URL="http://localhost:5000",
        HERMES_WS_URL="ws://localhost:5000",
    )
    @patch("requests.get")
    def test_check_hermes_health_unreachable(self, mock_get):
        mock_get.side_effect = requests.RequestException("Connection refused")

        result = check_hermes_health()
        self.assertTrue(result["configured"])
        self.assertEqual(result["status"], "unreachable")
        self.assertIn("error", result)

    @override_settings(HERMES_API_URL="")
    def test_check_hermes_health_not_configured(self):
        result = check_hermes_health()
        self.assertFalse(result["configured"])
        self.assertEqual(result["status"], "not_configured")


class SystemHealthViewEndpointsTests(SimpleTestCase):
    def setUp(self):
        self.client = APIClient()

    @patch("system.views.get_system_health_report")
    def test_system_health_view(self, mock_report):
        mock_report.return_value = {
            "status": "healthy",
            "timestamp": "2026-08-14T17:00:00Z",
            "version": "1.2.0",
            "services": {
                "atlas": {"status": "healthy"},
                "hermes": {"status": "healthy"},
            },
        }
        response = self.client.get(reverse("system-health"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("services", data)

    @patch("system.views.get_system_health_report")
    def test_system_health_view_fail_on_error(self, mock_report):
        mock_report.return_value = {
            "status": "unhealthy",
            "timestamp": "2026-08-14T17:00:00Z",
            "version": "1.2.0",
            "services": {
                "atlas": {"status": "unhealthy"},
                "hermes": {"status": "unhealthy"},
            },
        }
        response = self.client.get(reverse("system-health"), {"fail_on_error": "true"})
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)

    @patch("system.views.check_hermes_health")
    def test_hermes_health_view(self, mock_hermes):
        mock_hermes.return_value = {
            "configured": True,
            "status": "healthy",
            "api_url": "http://localhost:5000",
            "latency_ms": 2.5,
        }
        response = self.client.get(reverse("system-health-hermes"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["api_url"], "http://localhost:5000")

    @patch("system.views.get_atlas_services_health")
    def test_atlas_health_view(self, mock_atlas):
        mock_atlas.return_value = {
            "status": "healthy",
            "database": {"status": "healthy", "latency_ms": 1.1},
            "storage": {"enabled": False, "backend": "filesystem", "status": "healthy"},
            "email": {"configured": False, "status": "not_configured"},
            "chirpstack": {"configured": False, "status": "not_configured"},
            "firebase": {"configured": False, "status": "not_configured"},
        }
        response = self.client.get(reverse("system-health-atlas"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["database"]["status"], "healthy")
