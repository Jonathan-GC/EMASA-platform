from rest_framework import viewsets
from rest_framework.decorators import action

from .models import DeviceProfile, DeviceProfileTemplate, ApiUser
from .serializers import DeviceProfileSerializer, DeviceProfileTemplateSerializer, ApiUserSerializer

from roles.permissions import HasPermissionKey, IsAdminOrIsAuthenticatedReadOnly
from roles.mixins import PermissionKeyMixin
from roles.models import PermissionKey
from roles.serializers import PermissionKeySerializer

from chirpstack.chirpstack_api import sync_api_user_chirpstack_creation, sync_device_profile_chirpstack_creation

import logging

# Create your views here.

class DeviceProfileViewSet(viewsets.ModelViewSet, PermissionKeyMixin):
    queryset = DeviceProfile.objects.all()
    serializer_class = DeviceProfileSerializer
    permission_classes = [HasPermissionKey]
    scope = "device_profile"

    def perform_create(self, serializer):
        instance = serializer.save()
        self.create_permission_keys(instance, scope="device_profile")

        sync_response = sync_device_profile_chirpstack_creation(instance)

        if sync_response.status_code != 200:
            logging.error(f"Error al sincronizar el device_profile {instance.name} con Chirpstack: {sync_response.status_code} {instance.sync_error}")
        else:
            logging.info(f"Se ha sincronizado el device_profile {instance.cs_device_profile_id} - {instance.name} con Chirpstack")

    @action(detail=True, methods=["post"], permission_classes=[IsAdminOrIsAuthenticatedReadOnly])
    def regenerate_permission_keys(self, request, pk=None):
        instance = self.get_object()
        scope = "device_profile"

        self.create_permission_keys(instance, scope)

        permission_keys = PermissionKey.objects.filter(
            **{self.scope_field_map[scope]: instance}
        )
        serializer = PermissionKeySerializer(permission_keys, many=True)
        
        return Response(serializer.data)



class DeviceProfileTemplateViewSet(viewsets.ModelViewSet, PermissionKeyMixin):
    queryset = DeviceProfileTemplate.objects.all()
    serializer_class = DeviceProfileTemplateSerializer
    permission_classes = [HasPermissionKey]
    scope = "device_profile_template"

    def perform_create(self, serializer):
        instance = serializer.save()
        self.create_permission_keys(instance, scope="device_profile_template")
    
    @action(detail=True, methods=["post"], permission_classes=[IsAdminOrIsAuthenticatedReadOnly])
    def regenerate_permission_keys(self, request, pk=None):
        instance = self.get_object()
        scope = "device_profile_template"

        self.create_permission_keys(instance, scope)

        permission_keys = PermissionKey.objects.filter(
            **{self.scope_field_map[scope]: instance}
        )
        serializer = PermissionKeySerializer(permission_keys, many=True)
        
        return Response(serializer.data)

class ApiUserViewSet(viewsets.ModelViewSet, PermissionKeyMixin):
    queryset = ApiUser.objects.all()
    serializer_class = ApiUserSerializer
    permission_classes = [HasPermissionKey]
    scope = "api_user"

    def perform_create(self, serializer):
        instance = serializer.save()
        self.create_permission_keys(instance, scope="api_user")

        sync_response = sync_api_user_chirpstack_creation(instance)

        if sync_response.status_code != 200:
            logging.error(f"Error al sincronizar el api_user {instance.email} con Chirpstack: {sync_response.status_code} {instance.sync_error}")
        else:
            logging.info(f"Se ha sincronizado el api_user {instance.cs_user_id} - {instance.email} con Chirpstack")
    
    @action(detail=True, methods=["post"], permission_classes=[IsAdminOrIsAuthenticatedReadOnly])
    def regenerate_permission_keys(self, request, pk=None):
        instance = self.get_object()
        scope = "api_user"

        self.create_permission_keys(instance, scope)

        permission_keys = PermissionKey.objects.filter(
            **{self.scope_field_map[scope]: instance}
        )
        serializer = PermissionKeySerializer(permission_keys, many=True)
        
        return Response(serializer.data)

    
