"""
Unit tests for Service-to-Service Authentication

Run with:
    python manage.py test infrastructure.tests.test_service_auth
"""

from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from infrastructure.models import (
    Device, Machine, Type, Application, Gateway, Location, Measurements
)
from organizations.models import Tenant, Workspace
from chirpstack.models import DeviceProfile
import secrets

User = get_user_model()


class ServiceAuthenticationTestCase(TestCase):
    """Test cases for service-to-service authentication"""
    
    @classmethod
    def setUpTestData(cls):
        """Set up test data"""
        # Create test API key
        cls.valid_api_key = secrets.token_urlsafe(32)
        cls.invalid_api_key = "invalid-key"
        
        # Create tenant and workspace
        cls.tenant = Tenant.objects.create(
            name="Test Tenant",
            description="Test tenant for service auth"
        )
        cls.workspace = Workspace.objects.create(
            name="Test Workspace",
            description="Test workspace",
            tenant=cls.tenant
        )
        
        # Create device type
        cls.device_type = Type.objects.create(
            name="Test Type",
            description="Test device type"
        )
        
        # Create machine
        cls.machine = Machine.objects.create(
            name="Test Machine",
            description="Test machine",
            workspace=cls.workspace
        )
        
        # Create device profile
        cls.device_profile = DeviceProfile.objects.create(
            cs_device_profile_id="test-profile-id",
            name="Test Profile",
            workspace=cls.workspace
        )
        
        # Create application
        cls.application = Application.objects.create(
            cs_application_id="test-app-id",
            name="Test Application",
            description="Test application",
            device_type=cls.device_type,
            workspace=cls.workspace
        )
        
        # Create test device
        cls.device = Device.objects.create(
            dev_eui="1234567890abcdef",
            name="Test Device",
            description="Test device for service auth",
            machine=cls.machine,
            workspace=cls.workspace,
            device_type=cls.device_type,
            device_profile=cls.device_profile,
            application=cls.application
        )
        
        # Create measurements
        cls.measurement = Measurements.objects.create(
            device=cls.device,
            min=0.0,
            max=100.0,
            threshold=85.0,
            unit="PSI"
        )
    
    def setUp(self):
        """Set up test client"""
        self.client = APIClient()
    
    @override_settings(SERVICE_API_KEY=None)
    def test_metadata_endpoint_without_api_key_config(self):
        """Test that endpoint fails when SERVICE_API_KEY is not configured"""
        url = f'/api/devices/{self.device.id}/metadata/'
        
        # Try with any API key
        response = self.client.get(
            url,
            HTTP_X_API_KEY='some-key'
        )
        
        # Should return 401 because SERVICE_API_KEY is not configured
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('not configured', str(response.data))
    
    @override_settings(SERVICE_API_KEY='test-api-key-12345')
    def test_metadata_endpoint_with_valid_api_key(self):
        """Test that metadata endpoint works with valid API key"""
        url = f'/api/devices/{self.device.id}/metadata/'
        
        response = self.client.get(
            url,
            HTTP_X_API_KEY='test-api-key-12345'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify response structure
        data = response.json()
        self.assertEqual(data['dev_eui'], self.device.dev_eui)
        self.assertEqual(data['name'], self.device.name)
        self.assertIn('machine', data)
        self.assertIn('device_type', data)
        self.assertIn('application', data)
        self.assertIn('workspace', data)
        self.assertIn('measurements', data)
    
    @override_settings(SERVICE_API_KEY='test-api-key-12345')
    def test_metadata_endpoint_with_invalid_api_key(self):
        """Test that metadata endpoint rejects invalid API key"""
        url = f'/api/devices/{self.device.id}/metadata/'
        
        response = self.client.get(
            url,
            HTTP_X_API_KEY='wrong-api-key'
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('Invalid API Key', str(response.data))
    
    @override_settings(SERVICE_API_KEY='test-api-key-12345')
    def test_metadata_endpoint_without_api_key_header(self):
        """Test that metadata endpoint requires API key header"""
        url = f'/api/devices/{self.device.id}/metadata/'
        
        # Request without X-API-Key header
        response = self.client.get(url)
        
        # Should return 401 or 403 (not authenticated/not permitted)
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
        )
    
    @override_settings(SERVICE_API_KEY='test-api-key-12345')
    def test_metadata_endpoint_device_not_found(self):
        """Test that metadata endpoint returns 404 for non-existent device"""
        url = '/api/devices/999999/metadata/'
        
        response = self.client.get(
            url,
            HTTP_X_API_KEY='test-api-key-12345'
        )
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    @override_settings(SERVICE_API_KEY='test-api-key-12345')
    def test_metadata_response_structure(self):
        """Test that metadata response contains all required fields"""
        url = f'/api/devices/{self.device.id}/metadata/'
        
        response = self.client.get(
            url,
            HTTP_X_API_KEY='test-api-key-12345'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Check required fields
        required_fields = [
            'dev_eui', 'name', 'description', 'is_disabled', 'is_active',
            'enabled_activation', 'last_seen_at', 'machine', 'device_type',
            'application', 'workspace', 'device_profile', 'sync_status',
            'last_synced_at', 'measurements', 'activation'
        ]
        
        for field in required_fields:
            self.assertIn(field, data, f"Field '{field}' not in response")
        
        # Check nested structures
        self.assertIn('id', data['machine'])
        self.assertIn('name', data['machine'])
        self.assertIn('id', data['device_type'])
        self.assertIn('name', data['device_type'])
        self.assertIn('id', data['application'])
        self.assertIn('id', data['workspace'])
        
        # Check measurements
        self.assertIsInstance(data['measurements'], list)
        if len(data['measurements']) > 0:
            measurement = data['measurements'][0]
            self.assertIn('min', measurement)
            self.assertIn('max', measurement)
            self.assertIn('threshold', measurement)
            self.assertIn('unit', measurement)
    
    @override_settings(SERVICE_API_KEY='test-api-key-12345')
    def test_metadata_does_not_expose_sensitive_activation_keys(self):
        """Test that sensitive activation keys are not exposed"""
        from infrastructure.models import Activation
        
        # Create activation for device
        activation = Activation.objects.create(
            afcntdown=0,
            app_s_key="SENSITIVE_APP_KEY",
            dev_addr="260CB229",
            f_cnt_up=0,
            f_nwk_s_int_key="SENSITIVE_FNwk_KEY",
            n_f_cnt_down=0,
            nwk_s_enc_key="SENSITIVE_NWK_KEY",
            s_nwk_s_int_key="SENSITIVE_SNwk_KEY"
        )
        self.device.activation = activation
        self.device.save()
        
        url = f'/api/devices/{self.device.id}/metadata/'
        
        response = self.client.get(
            url,
            HTTP_X_API_KEY='test-api-key-12345'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Verify activation data is present but sensitive keys are not
        self.assertIsNotNone(data['activation'])
        self.assertIn('dev_addr', data['activation'])
        self.assertIn('f_cnt_up', data['activation'])
        
        # Verify sensitive keys are NOT present
        response_text = str(response.content)
        self.assertNotIn('SENSITIVE_APP_KEY', response_text)
        self.assertNotIn('SENSITIVE_FNwk_KEY', response_text)
        self.assertNotIn('SENSITIVE_NWK_KEY', response_text)
        self.assertNotIn('SENSITIVE_SNwk_KEY', response_text)
        
        # Verify the keys are not in the activation dict
        activation_data = data['activation']
        self.assertNotIn('app_s_key', activation_data)
        self.assertNotIn('f_nwk_s_int_key', activation_data)
        self.assertNotIn('nwk_s_enc_key', activation_data)
        self.assertNotIn('s_nwk_s_int_key', activation_data)
    
    @override_settings(SERVICE_API_KEY='test-api-key-12345')
    def test_service_auth_does_not_interfere_with_other_endpoints(self):
        """Test that service auth doesn't affect other device endpoints"""
        # Create a regular user
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Try to access regular device list endpoint (should work with JWT)
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        
        # This should work with JWT authentication (not service auth)
        response = self.client.get(
            '/api/devices/',
            HTTP_AUTHORIZATION=f'Bearer {access_token}'
        )
        
        # Should get 200 or 403 (depending on permissions), not 401
        self.assertNotEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ServiceAuthenticationEdgeCasesTestCase(TestCase):
    """Test edge cases for service authentication"""
    
    @override_settings(SERVICE_API_KEY='test-key')
    def test_api_key_with_spaces(self):
        """Test that API keys with leading/trailing spaces are rejected"""
        client = APIClient()
        
        # Create minimal test data
        tenant = Tenant.objects.create(name="Test", description="Test")
        workspace = Workspace.objects.create(
            name="Test", description="Test", tenant=tenant
        )
        device_type = Type.objects.create(name="Type", description="Type")
        machine = Machine.objects.create(
            name="Machine", description="Machine", workspace=workspace
        )
        device_profile = DeviceProfile.objects.create(
            cs_device_profile_id="profile",
            name="Profile",
            workspace=workspace
        )
        application = Application.objects.create(
            cs_application_id="app",
            name="App",
            description="App",
            device_type=device_type,
            workspace=workspace
        )
        device = Device.objects.create(
            dev_eui="1234567890abcdef",
            name="Device",
            description="Device",
            machine=machine,
            workspace=workspace,
            device_type=device_type,
            device_profile=device_profile,
            application=application
        )
        
        url = f'/api/devices/{device.id}/metadata/'
        
        # API key with leading space
        response = client.get(url, HTTP_X_API_KEY=' test-key')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # API key with trailing space
        response = client.get(url, HTTP_X_API_KEY='test-key ')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    @override_settings(SERVICE_API_KEY='test-key')
    def test_case_sensitive_api_key(self):
        """Test that API key validation is case-sensitive"""
        client = APIClient()
        
        # Reuse previous test data
        tenant = Tenant.objects.create(name="Test2", description="Test")
        workspace = Workspace.objects.create(
            name="Test2", description="Test", tenant=tenant
        )
        device_type = Type.objects.create(name="Type2", description="Type")
        machine = Machine.objects.create(
            name="Machine2", description="Machine", workspace=workspace
        )
        device_profile = DeviceProfile.objects.create(
            cs_device_profile_id="profile2",
            name="Profile2",
            workspace=workspace
        )
        application = Application.objects.create(
            cs_application_id="app2",
            name="App2",
            description="App",
            device_type=device_type,
            workspace=workspace
        )
        device = Device.objects.create(
            dev_eui="abcdef1234567890",
            name="Device2",
            description="Device",
            machine=machine,
            workspace=workspace,
            device_type=device_type,
            device_profile=device_profile,
            application=application
        )
        
        url = f'/api/devices/{device.id}/metadata/'
        
        # Wrong case should fail
        response = client.get(url, HTTP_X_API_KEY='TEST-KEY')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Correct case should succeed
        response = client.get(url, HTTP_X_API_KEY='test-key')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
