from django.test import TestCase
from unittest.mock import patch, MagicMock, ANY
import requests
from organizations.models import Tenant, Subscription, Workspace
from infrastructure.models import Gateway, Location, Device, Application, Type
from chirpstack.chirpstack_api import (
    test_connection,
    reset_connection_cache,
    sync_tenant_get,
    sync_gateway_get,
    sync_device_get,
    get_tenant_from_chirpstack,
    cs_get,
    cs_post,
    CHIRPSTACK_API_URL,
    CHIRPSTACK_TENANT_URL,
)
from django.core.management import call_command
import io


class ChirpStackConnectionTests(TestCase):
    def setUp(self):
        reset_connection_cache()
        self.subscription = Subscription.objects.create(
            name="Test Sub", description="Desc"
        )
        self.tenant = Tenant.objects.create(
            name="Test Tenant",
            subscription=self.subscription,
            cs_tenant_id="test-cs-id-123",
        )
        self.workspace = Workspace.objects.create(
            name="Test Workspace",
            tenant=self.tenant,
        )
        self.location = Location.objects.create(name="Test Loc")
        self.gateway = Gateway.objects.create(
            cs_gateway_id="0011223344556677",
            name="Test GW",
            workspace=self.workspace,
            location=self.location,
        )

    def tearDown(self):
        reset_connection_cache()

    @patch("chirpstack.chirpstack_api.requests.get")
    def test_connection_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        self.assertTrue(test_connection(force=True))
        mock_get.assert_called_with(CHIRPSTACK_API_URL, headers=ANY, timeout=10)

    @patch("chirpstack.chirpstack_api.requests.get")
    def test_connection_failure_on_error_code(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_get.return_value = mock_response

        self.assertFalse(test_connection(force=True))

    @patch("chirpstack.chirpstack_api.requests.get")
    def test_connection_failure_on_exception(self, mock_get):
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")

        self.assertFalse(test_connection(force=True))

    @patch("chirpstack.chirpstack_api.requests.get")
    def test_connection_caching_within_ttl(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # First call triggers network
        self.assertTrue(test_connection(force=True))
        self.assertEqual(mock_get.call_count, 1)

        # Second call within TTL uses cached result
        self.assertTrue(test_connection(cached=True, cache_ttl=10))
        self.assertEqual(mock_get.call_count, 1)

        # Force call bypasses cache
        self.assertTrue(test_connection(force=True))
        self.assertEqual(mock_get.call_count, 2)

    @patch("chirpstack.chirpstack_api.test_connection", return_value=False)
    @patch("chirpstack.chirpstack_api.requests.request")
    def test_sync_tenant_checks_connection_first_and_aborts(
        self, mock_requests_req, mock_test_conn
    ):
        result = sync_tenant_get(self.tenant)
        self.assertIsNone(result)
        mock_test_conn.assert_called()
        mock_requests_req.assert_not_called()
        self.tenant.refresh_from_db()
        self.assertEqual(self.tenant.sync_status, "ERROR")
        self.assertIn("Unable to connect", self.tenant.sync_error)

    @patch("chirpstack.chirpstack_api.test_connection", return_value=False)
    @patch("chirpstack.chirpstack_api.requests.request")
    def test_sync_gateway_checks_connection_first_and_aborts(
        self, mock_requests_req, mock_test_conn
    ):
        result = sync_gateway_get(self.gateway)
        self.assertIsNone(result)
        mock_test_conn.assert_called()
        mock_requests_req.assert_not_called()
        self.gateway.refresh_from_db()
        self.assertEqual(self.gateway.sync_status, "ERROR")

    @patch("chirpstack.chirpstack_api.test_connection", return_value=False)
    @patch("chirpstack.chirpstack_api.requests.request")
    def test_get_tenant_from_chirpstack_checks_connection_and_aborts(
        self, mock_requests_req, mock_test_conn
    ):
        result = get_tenant_from_chirpstack()
        self.assertIsNone(result)
        mock_test_conn.assert_called()
        mock_requests_req.assert_not_called()

    @patch("chirpstack.chirpstack_api.test_connection", return_value=False)
    @patch("chirpstack.chirpstack_api.requests.request")
    def test_chirpstack_request_helpers_block_when_unreachable(
        self, mock_requests_req, mock_test_conn
    ):
        get_res = cs_get("http://example.com/api/test")
        self.assertIsNone(get_res)
        post_res = cs_post("http://example.com/api/test", json={"key": "val"})
        self.assertIsNone(post_res)
        mock_requests_req.assert_not_called()

    @patch("chirpstack.management.commands.rm_cs_duplicates.test_connection", return_value=False)
    @patch("chirpstack.management.commands.rm_cs_duplicates.requests.get")
    def test_rm_cs_duplicates_checks_connection_and_aborts(
        self, mock_requests_get, mock_test_conn
    ):
        out = io.StringIO()
        call_command("rm_cs_duplicates", stdout=out)
        mock_test_conn.assert_called()
        mock_requests_get.assert_not_called()
        self.assertIn("Unable to connect", out.getvalue())
