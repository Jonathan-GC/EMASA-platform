from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser

from .models import Workspace, Organization, Region
from .serializers import WorkspaceSerializer, OrganizationSerializer, RegionSerializer

from roles.permissions import IsAdminOrIsAuthenticatedReadOnly, HasPermissionKey
from roles.mixins import PermissionKeyMixin

from rest_framework.decorators import action
from rest_framework.response import Response

from roles.models import PermissionKey
from roles.serializers import PermissionKeySerializer

class WorkspaceViewSet(viewsets.ModelViewSet, PermissionKeyMixin):
    queryset = Workspace.objects.all()
    serializer_class = WorkspaceSerializer
    permission_classes = [HasPermissionKey]
    scope = "workspace"

    def perform_create(self, serializer):
        instance = serializer.save()
        self.create_permission_keys(instance, scope="workspace")

    @action(detail=True, methods=["post"], permission_classes=[IsAdminOrIsAuthenticatedReadOnly])
    def regenerate_permission_keys(self, request, pk=None):
        instance = self.get_object()
        scope = "workspace"

        self.create_permission_keys(instance, scope)

        permission_keys = PermissionKey.objects.filter(
            **{self.scope_field_map[scope]: instance}
        )
        serializer = PermissionKeySerializer(permission_keys, many=True)
        
        return Response(serializer.data)

class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = [IsAdminOrIsAuthenticatedReadOnly]


class RegionViewSet(viewsets.ModelViewSet, PermissionKeyMixin):
    queryset = Region.objects.all()
    serializer_class = RegionSerializer
    permission_classes = [HasPermissionKey]
    scope = "region"

    def perform_create(self, serializer):
        instance = serializer.save()
        self.create_permission_keys(instance, scope="region")

    @action(detail=True, methods=["post"], permission_classes=[IsAdminOrIsAuthenticatedReadOnly])
    def regenerate_permission_keys(self, request, pk=None):
        instance = self.get_object()
        scope = "region"

        self.create_permission_keys(instance, scope)

        permission_keys = PermissionKey.objects.filter(
            **{self.scope_field_map[scope]: instance}
        )
        serializer = PermissionKeySerializer(permission_keys, many=True)
        
        return Response(serializer.data)
