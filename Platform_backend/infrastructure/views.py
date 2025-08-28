from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .serializers import GatewaySerializer, MachineSerializer, TypeSerializer, DeviceSerializer, ApplicationSerializer, LocationSerializer
from .models import Gateway, Machine, Type, Device, Application, Location

from roles.permissions import HasPermissionKey, IsAdminOrIsAuthenticatedReadOnly
from roles.mixins import PermissionKeyMixin
from roles.models import PermissionKey
from roles.serializers import PermissionKeySerializer

from chirpstack.chirpstack_api import sync_gateway_chirpstack

import logging

class GatewayViewSet(viewsets.ModelViewSet, PermissionKeyMixin):
    queryset = Gateway.objects.all()
    serializer_class = GatewaySerializer
    permission_classes = [HasPermissionKey]
    scope = "gateway"

    def perform_create(self, serializer):
        instance = serializer.save()
        self.create_permission_keys(instance, scope="gateway")

        sync_response = sync_gateway_chirpstack(instance, request=self.request)

        if sync_response.status_code != 200:
            logging.error(f"Error al crear el gateway {instance.name} con Chirpstack: {sync_response.status_code} {instance.sync_error}")
        else:
            logging.info(f"Se ha sincronizado el gateway {instance.cs_gateway_id} - {instance.name} con Chirpstack")

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve a gateway and sync it with Chirpstack before returning the response.

        """
        instance = self.get_object()

        sync_gateway_chirpstack(instance, request)
        instance.refresh_from_db()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        """
        List a queryset of gateways and sync each one with Chirpstack before
        returning the response.

        """
    
        queryset = self.filter_queryset(self.get_queryset())

        for gateway in queryset:
            sync_gateway_chirpstack(gateway, request)
            gateway.refresh_from_db()

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def perform_update(self, serializer):
        """
        Update a gateway and sync it with Chirpstack.

        Args:
            serializer: a GatewaySerializer instance

        """
        instance = serializer.save()

        sync_response = sync_gateway_chirpstack(instance, request=self.request)

        if sync_response.status_code != 200:
            logging.error(f"Error al actualizar el gateway {instance.name} con Chirpstack: {sync_response.status_code} {instance.sync_error}")
        else:
            logging.info(f"Se ha sincronizado el gateway {instance.cs_gateway_id} - {instance.name} con Chirpstack")
        
    def perform_destroy(self, instance):
        sync_response = sync_gateway_chirpstack(instance, request=self.request)

        if sync_response.status_code != 200:
            logging.error(f"Error al eliminar el gateway {instance.name} con Chirpstack: {sync_response.status_code} {instance.sync_error}")
        else:
            logging.info(f"Se ha sincronizado el gateway {instance.cs_gateway_id} - {instance.name} con Chirpstack")
        
        instance.delete()

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
