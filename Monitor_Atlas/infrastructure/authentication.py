"""
Service-to-Service Authentication for Monitor Atlas API

This module provides API Key authentication for service-to-service communication,
specifically designed for Monitor_Hermes to consume Monitor_Atlas endpoints securely.
"""

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.conf import settings


class ServiceAPIKeyAuthentication(BaseAuthentication):
    """
    Authentication class for service-to-service communication using API Key.
    
    This authentication method verifies that incoming requests include a valid
    API Key in the X-API-Key header, matching the shared secret stored in
    SERVICE_API_KEY environment variable.
    
    Usage:
        In a ViewSet or APIView:
        authentication_classes = [ServiceAPIKeyAuthentication]
        permission_classes = [IsServiceAuthenticated]
        
    Expected header format:
        X-API-Key: <your-secret-api-key>
    """
    
    keyword = 'X-API-Key'
    
    def authenticate(self, request):
        """
        Authenticate the request using API Key from X-API-Key header.
        
        Args:
            request: DRF Request object
            
        Returns:
            tuple: (None, dict) with service information if authentication succeeds
            None: If X-API-Key header is not present (allows other auth methods)
            
        Raises:
            AuthenticationFailed: If API Key is invalid or SERVICE_API_KEY is not configured
        """
        api_key = request.META.get('HTTP_X_API_KEY')
        
        # If no API Key header is present, return None to allow other authentication methods
        if not api_key:
            return None
        
        # Get the configured service API key from settings
        service_api_key = getattr(settings, 'SERVICE_API_KEY', None)
        
        if not service_api_key:
            raise AuthenticationFailed(
                'Service API Key not configured. Please set SERVICE_API_KEY environment variable.'
            )
        
        # Validate the provided API key
        if api_key != service_api_key:
            raise AuthenticationFailed('Invalid API Key.')
        
        # Return None as user (no user authentication) and service info as auth
        # This allows the permission class to identify service-to-service requests
        service_info = {
            'service': 'authenticated',
            'type': 'service_to_service',
            'client': 'monitor_hermes'
        }
        
        return (None, service_info)
    
    def authenticate_header(self, request):
        """
        Return a string to be used as the value of the WWW-Authenticate
        header in a 401 Unauthenticated response.
        """
        return self.keyword
