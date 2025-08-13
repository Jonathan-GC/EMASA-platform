from rest_framework import viewsets

from .serializers import GatewaySerializer, MachineSerializer, NodeTypeSerializer, NodeSerializer, ServiceSerializer
from .models import Gateway, Machine, NodeType, Node, Service

from roles.permissions import HasPermissionKey, IsAdminOrIsAuthenticatedReadOnly
from roles.mixins import PermissionKeyMixin

from rest_framework.decorators import action
from rest_framework.response import Response

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

class NodeTypeViewSet(viewsets.ModelViewSet):
    queryset = NodeType.objects.all()
    serializer_class = NodeTypeSerializer
    permission_classes = [IsAdminOrIsAuthenticatedReadOnly]

class NodeViewSet(viewsets.ModelViewSet, PermissionKeyMixin):
    queryset = Node.objects.all()
    serializer_class = NodeSerializer
    permission_classes = [HasPermissionKey]
    scope = "node"

    def perform_create(self, serializer):
        instance = serializer.save()
        self.create_permission_keys(instance, scope="node")
    
    @action(detail=True, methods=["post"], permission_classes=[IsAdminOrIsAuthenticatedReadOnly])
    def regenerate_permission_keys(self, request, pk=None):
        instance = self.get_object()
        scope = "node"

        self.create_permission_keys(instance, scope)

        permission_keys = PermissionKey.objects.filter(
            **{self.scope_field_map[scope]: instance}
        )
        serializer = PermissionKeySerializer(permission_keys, many=True)
        
        return Response(serializer.data)

class ServiceViewSet(viewsets.ModelViewSet, PermissionKeyMixin):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    permission_classes = [HasPermissionKey]
    scope = "service"

    def perform_create(self, serializer):
        instance = serializer.save()
        self.create_permission_keys(instance, scope="service")

    @action(detail=True, methods=["post"], permission_classes=[IsAdminOrIsAuthenticatedReadOnly])
    def regenerate_permission_keys(self, request, pk=None):
        instance = self.get_object()
        scope = "service"

        self.create_permission_keys(instance, scope)

        permission_keys = PermissionKey.objects.filter(
            **{self.scope_field_map[scope]: instance}
        )
        serializer = PermissionKeySerializer(permission_keys, many=True)
        
        return Response(serializer.data)
