from rest_framework import viewsets

from .permissions import HasPermissionKey, IsAdminOrIsAuthenticatedReadOnly

from .serializers import PermissionKeySerializer, RoleSerializer, WorkspaceMembershipSerializer, RolePermissionSerializer
from .models import PermissionKey, Role, WorkspaceMembership, RolePermission
from .mixins import PermissionKeyMixin

from rest_framework.decorators import action
from rest_framework.response import Response

class PermissionKeyViewSet(viewsets.ModelViewSet):

    queryset = PermissionKey.objects.all()
    serializer_class = PermissionKeySerializer
    permission_classes = [IsAdminOrIsAuthenticatedReadOnly]


class RoleViewSet(viewsets.ModelViewSet, PermissionKeyMixin):

    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [HasPermissionKey]
    scope = "role"

    def perform_create(self, serializer):
        instance = serializer.save()
        self.create_permission_keys(instance, scope="role")

    @action(detail=False, methods=["get"])
    def get_all_permission_keys_by_role(self, request):
        role_id = request.query_params.get("role_id")
        permission_keys = PermissionKey.objects.filter(role_id=role_id)
        serializer = PermissionKeySerializer(permission_keys, many=True)
        return self.get_paginated_response(serializer.data)
    
    @action(detail=True, methods=["post"], permission_classes=[IsAdminOrIsAuthenticatedReadOnly])
    def regenerate_permission_keys(self, request, pk=None):
        instance = self.get_object()
        scope = "role"

        self.create_permission_keys(instance, scope)

        permission_keys = PermissionKey.objects.filter(
            **{self.scope_field_map[scope]: instance}
        )
        serializer = PermissionKeySerializer(permission_keys, many=True)
        
        return Response(serializer.data)

class WorkspaceMembershipViewSet(viewsets.ModelViewSet, PermissionKeyMixin):

    queryset = WorkspaceMembership.objects.all()
    serializer_class = WorkspaceMembershipSerializer
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

class RolePermissionViewSet(viewsets.ModelViewSet):

    queryset = RolePermission.objects.all()
    serializer_class = RolePermissionSerializer
    permission_classes = [IsAdminOrIsAuthenticatedReadOnly]

        