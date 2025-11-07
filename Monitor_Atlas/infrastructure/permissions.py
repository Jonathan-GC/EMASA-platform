"""
Service-to-Service Permission Classes

This module provides permission classes for service-to-service authenticated requests.
"""

from rest_framework.permissions import BasePermission


class IsServiceAuthenticated(BasePermission):
    """
    Permission class to verify that the request is authenticated via service API Key.
    
    This permission checks that:
    1. The request has auth information (set by ServiceAPIKeyAuthentication)
    2. The auth type is 'service_to_service'
    
    Usage:
        class MyViewSet(viewsets.ModelViewSet):
            authentication_classes = [ServiceAPIKeyAuthentication]
            permission_classes = [IsServiceAuthenticated]
            
    This ensures only service-to-service requests with valid API Keys can access the endpoint.
    """
    
    def has_permission(self, request, view):
        """
        Check if the request has valid service authentication.
        
        Args:
            request: DRF Request object
            view: The view being accessed
            
        Returns:
            bool: True if request is authenticated as a service, False otherwise
        """
        # Check if request.auth exists and contains service information
        if not request.auth:
            return False
        
        # Verify that the authentication type is service_to_service
        if not isinstance(request.auth, dict):
            return False
        
        # Check that it's marked as service_to_service authentication
        if request.auth.get('type') != 'service_to_service':
            return False
        
        # Check that service is authenticated
        if request.auth.get('service') != 'authenticated':
            return False
        
        return True
    
    def has_object_permission(self, request, view, obj):
        """
        Object-level permission check.
        
        Since this is service-to-service authentication, we grant access
        at the object level as well if the request passes has_permission.
        
        Args:
            request: DRF Request object
            view: The view being accessed
            obj: The object being accessed
            
        Returns:
            bool: True if service is authenticated
        """
        return self.has_permission(request, view)
