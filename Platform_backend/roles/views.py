from rest_framework import viewsets

from .permissions import HasPermissionKey

from .serializers import PermissionKeySerializer, RoleSerializer, WorkspaceMembershipSerializer, RolePermissionSerializer
from .models import PermissionKey, Role, WorkspaceMembership, RolePermission
from .mixins import PermissionKeyMixin


class PermissionKeyViewSet(viewsets.ModelViewSet):

    queryset = PermissionKey.objects.all()
    serializer_class = PermissionKeySerializer
    permission_classes = [HasPermissionKey]
    scope = "pemission_key"


class RoleViewSet(viewsets.ModelViewSet, PermissionKeyMixin):

    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [HasPermissionKey]
    scope = "role"

    def perform_create(self, serializer):
        instance = serializer.save()
        self.create_permission_keys(instance, scope="role")

class WorkspaceMembershipViewSet(viewsets.ModelViewSet, PermissionKeyMixin):

    queryset = WorkspaceMembership.objects.all()
    serializer_class = WorkspaceMembershipSerializer
    permission_classes = [HasPermissionKey]
    scope = "workspace"

    def perform_create(self, serializer):
        instance = serializer.save()
        self.create_permission_keys(instance, scope="workspace")

class RolePermissionViewSet(viewsets.ModelViewSet):

    queryset = RolePermission.objects.all()
    serializer_class = RolePermissionSerializer
    permission_classes = [HasPermissionKey]
    scope = "role_permission"

        