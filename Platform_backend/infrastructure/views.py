from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .serializers import GatewaySerializer, MachineSerializer, TypeSerializer, DeviceSerializer, ApplicationSerializer, LocationSerializer
from .models import Gateway, Machine, Type, Device, Application, Location

from roles.permissions import HasPermissionKey, IsAdminOrIsAuthenticatedReadOnly
from roles.mixins import PermissionKeyMixin
from roles.models import PermissionKey
from roles.serializers import PermissionKeySerializer

class GatewayViewSet(viewsets.ModelViewSet, PermissionKeyMixin):
    queryset = Gateway.objects.all()
    serializer_class = GatewaySerializer
    permission_classes = [HasPermissionKey]
    scope = "gateway"

    def perform_create(self, serializer):
        instance = serializer.save()
        self.create_permission_keys(instance, scope="gateway")
    
    @action(detail=True, methods=["post"], permission_classes=[IsAdminOrIsAuthenticatedReadOnly])
    def regenerate_permission_keys(self, request, pk=None):
        instance = self.get_object()
        scope = "gateway"

        self.create_permission_keys(instance, scope)

        permission_keys = PermissionKey.objects.filter(
            **{self.scope_field_map[scope]: instance}
        )
        serializer = PermissionKeySerializer(permission_keys, many=True)
        
        return Response(serializer.data)
    


class MachineViewSet(viewsets.ModelViewSet, PermissionKeyMixin):
    queryset = Machine.objects.all()
    serializer_class = MachineSerializer
    permission_classes = [HasPermissionKey]
    scope = "machine"

    def perform_create(self, serializer):
        instance = serializer.save()
        self.create_permission_keys(instance, scope="machine")
    
    @action(detail=True, methods=["post"], permission_classes=[IsAdminOrIsAuthenticatedReadOnly])
    def regenerate_permission_keys(self, request, pk=None):
        instance = self.get_object()
        scope = "machine"

        self.create_permission_keys(instance, scope)

        permission_keys = PermissionKey.objects.filter(
            **{self.scope_field_map[scope]: instance}
        )
        serializer = PermissionKeySerializer(permission_keys, many=True)
        
        return Response(serializer.data)
    
    @action(detail=True, methods=["patch"], permission_classes=[HasPermissionKey])
    def set_machine_image(self, request, pk=None):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

class TypeViewSet(viewsets.ModelViewSet, PermissionKeyMixin):
    queryset = Type.objects.all()
    serializer_class = TypeSerializer
    permission_classes = [HasPermissionKey]
    scope = "type"

    def perform_create(self, serializer):
        instance = serializer.save()
        self.create_permission_keys(instance, scope="type")
    
    @action(detail=True, methods=["post"], permission_classes=[IsAdminOrIsAuthenticatedReadOnly])
    def regenerate_permission_keys(self, request, pk=None):
        instance = self.get_object()
        scope = "type"

        self.create_permission_keys(instance, scope)

        permission_keys = PermissionKey.objects.filter(
            **{self.scope_field_map[scope]: instance}
        )
        serializer = PermissionKeySerializer(permission_keys, many=True)
        
        return Response(serializer.data)
    
    @action(detail=True, methods=["patch"], permission_classes=[HasPermissionKey])
    def set_type_image(self, request, pk=None):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

class DeviceViewSet(viewsets.ModelViewSet, PermissionKeyMixin):
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer
    permission_classes = [HasPermissionKey]
    scope = "device"

    def perform_create(self, serializer):
        instance = serializer.save()
        self.create_permission_keys(instance, scope="device")
    
    @action(detail=True, methods=["post"], permission_classes=[IsAdminOrIsAuthenticatedReadOnly])
    def regenerate_permission_keys(self, request, pk=None):
        instance = self.get_object()
        scope = "device"

        self.create_permission_keys(instance, scope)

        permission_keys = PermissionKey.objects.filter(
            **{self.scope_field_map[scope]: instance}
        )
        serializer = PermissionKeySerializer(permission_keys, many=True)
        
        return Response(serializer.data)

class ApplicationViewSet(viewsets.ModelViewSet, PermissionKeyMixin):
    queryset = Application.objects.all()
    serializer_class = ApplicationSerializer
    permission_classes = [HasPermissionKey]
    scope = "application"

    def perform_create(self, serializer):
        instance = serializer.save()
        self.create_permission_keys(instance, scope="application")

    @action(detail=True, methods=["post"], permission_classes=[IsAdminOrIsAuthenticatedReadOnly])
    def regenerate_permission_keys(self, request, pk=None):
        instance = self.get_object()
        scope = "application"

        self.create_permission_keys(instance, scope)

        permission_keys = PermissionKey.objects.filter(
            **{self.scope_field_map[scope]: instance}
        )
        serializer = PermissionKeySerializer(permission_keys, many=True)
        
        return Response(serializer.data)
    

class LocationViewSet(viewsets.ModelViewSet, PermissionKeyMixin):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    permission_classes = [HasPermissionKey]
    scope = "location"

    def perform_create(self, serializer):
        instance = serializer.save()
        self.create_permission_keys(instance, scope="location")

    @action(detail=True, methods=["post"], permission_classes=[IsAdminOrIsAuthenticatedReadOnly])
    def regenerate_permission_keys(self, request, pk=None):
        instance = self.get_object()
        scope = "location"

        self.create_permission_keys(instance, scope)

        permission_keys = PermissionKey.objects.filter(
            **{self.scope_field_map[scope]: instance}
        )
        serializer = PermissionKeySerializer(permission_keys, many=True)
        
        return Response(serializer.data)
