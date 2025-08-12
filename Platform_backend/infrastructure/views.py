from rest_framework import viewsets

from .serializers import GatewaySerializer, MachineSerializer, NodeTypeSerializer, NodeSerializer, ServiceSerializer
from .models import Gateway, Machine, NodeType, Node, Service

from roles.permissions import HasPermissionKey, IsAdminOrIsAuthenticatedReadOnly
from roles.mixins import PermissionKeyMixin

class GatewayViewSet(viewsets.ModelViewSet, PermissionKeyMixin):
    queryset = Gateway.objects.all()
    serializer_class = GatewaySerializer
    permission_classes = [HasPermissionKey]
    scope = "gateway"

    def perform_create(self, serializer):
        instance = serializer.save()
        self.create_permission_keys(instance, scope="gateway")

class MachineViewSet(viewsets.ModelViewSet, PermissionKeyMixin):
    queryset = Machine.objects.all()
    serializer_class = MachineSerializer
    permission_classes = [HasPermissionKey]
    scope = "machine"

    def perform_create(self, serializer):
        instance = serializer.save()
        self.create_permission_keys(instance, scope="machine")

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

class ServiceViewSet(viewsets.ModelViewSet, PermissionKeyMixin):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    permission_classes = [HasPermissionKey]
    scope = "service"

    def perform_create(self, serializer):
        instance = serializer.save()
        self.create_permission_keys(instance, scope="service")
