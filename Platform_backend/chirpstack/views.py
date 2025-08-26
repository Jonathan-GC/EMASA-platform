from rest_framework import viewsets
from rest_framework.decorators import action

from .models import DeviceProfile, DeviceProfileTemplate, ApiUser
from .serializers import DeviceProfileSerializer, DeviceProfileTemplateSerializer, ApiUserSerializer

from roles.permissions import HasPermissionKey, IsAdminOrIsAuthenticatedReadOnly
from roles.mixins import PermissionKeyMixin
from roles.models import PermissionKey
from roles.serializers import PermissionKeySerializer


# Create your views here.

class DeviceProfileViewSet(viewsets.ModelViewSet, PermissionKeyMixin):
    queryset = DeviceProfile.objects.all()
    serializer_class = DeviceProfileSerializer
    permission_classes = [HasPermissionKey]
    scope = "device_profile"

    def perform_create(self, serializer):
        instance = serializer.save()
        self.create_permission_keys(instance, scope="device_profile")

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

    
