from rest_framework import viewsets

from .serializers import GatewaySerializer, MachineSerializer, NodeTypeSerializer, NodeSerializer, ServiceSerializer
from .models import Gateway, Machine, NodeType, Node, Service

from roles.permissions import HasPermissionKey, IsAdminOrIsAuthenticatedReadOnly

class GatewayViewSet(viewsets.ModelViewSet):
    queryset = Gateway.objects.all()
    serializer_class = GatewaySerializer
    permission_classes = [HasPermissionKey]
    scope = "gateway"

class MachineViewSet(viewsets.ModelViewSet):
    queryset = Machine.objects.all()
    serializer_class = MachineSerializer
    permission_classes = [HasPermissionKey]
    scope = "machine"

class NodeTypeViewSet(viewsets.ModelViewSet):
    queryset = NodeType.objects.all()
    serializer_class = NodeTypeSerializer
    permission_classes = [IsAdminOrIsAuthenticatedReadOnly]

class NodeViewSet(viewsets.ModelViewSet):
    queryset = Node.objects.all()
    serializer_class = NodeSerializer
    permission_classes = [HasPermissionKey]
    scope = "node"

class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    permission_classes = [HasPermissionKey]
    scope = "service"
