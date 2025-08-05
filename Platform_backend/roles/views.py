from rest_framework import viewsets

from .permissions import HasPermissionKey

from .serializers import PermissionKeySerializer, RoleSerializer, WorkspaceMembershipSerializer, RolePermissionSerializer
from .models import PermissionKey, Role, WorkspaceMembership, RolePermission


class PermissionKeyViewSet(viewsets.ModelViewSet):

    queryset = PermissionKey.objects.all()
    serializer_class = PermissionKeySerializer
    permission_classes = [HasPermissionKey]
    scope = "pemission_key"

class RoleViewSet(viewsets.ModelViewSet):

    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [HasPermissionKey]
    scope = "role"

class WorkspaceMembershipViewSet(viewsets.ModelViewSet):

    queryset = WorkspaceMembership.objects.all()
    serializer_class = WorkspaceMembershipSerializer
    permission_classes = [HasPermissionKey]
    scope = "workspace"

class RolePermissionViewSet(viewsets.ModelViewSet):

    queryset = RolePermission.objects.all()
    serializer_class = RolePermissionSerializer
    permission_classes = [HasPermissionKey]
    scope = "role"

        