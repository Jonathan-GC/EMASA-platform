from rest_framework import viewsets

from .permissions import HasPermissionKey, IsAdminOrIsAuthenticatedReadOnly

from .serializers import (
    PermissionKeySerializer,
    RoleSerializer,
    WorkspaceMembershipSerializer,
    RolePermissionSerializer,
)
from .models import PermissionKey, Role, WorkspaceMembership, RolePermission
from .mixins import PermissionKeyMixin

from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema_view, extend_schema


class PermissionKeyViewSet(viewsets.ModelViewSet):

    queryset = PermissionKey.objects.all()
    serializer_class = PermissionKeySerializer
    permission_classes = [IsAdminOrIsAuthenticatedReadOnly]


@extend_schema_view(
    list=extend_schema(description="Role List"),
    create=extend_schema(description="Role Create"),
    retrieve=extend_schema(description="Role Retrieve"),
    update=extend_schema(description="Role Update"),
    partial_update=extend_schema(description="Role Partial Update"),
    destroy=extend_schema(description="Role Destroy"),
    get_all_permission_keys_by_role=extend_schema(
        description="Get all permission keys by role ID"
    ),
)
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


@extend_schema_view(
    list=extend_schema(description="Workspace Membership List"),
    create=extend_schema(description="Workspace Membership Create"),
    retrieve=extend_schema(description="Workspace Membership Retrieve"),
    update=extend_schema(description="Workspace Membership Update"),
    partial_update=extend_schema(description="Workspace Membership Partial Update"),
    destroy=extend_schema(description="Workspace Membership Destroy"),
)
class WorkspaceMembershipViewSet(viewsets.ModelViewSet, PermissionKeyMixin):

    queryset = WorkspaceMembership.objects.all()
    serializer_class = WorkspaceMembershipSerializer
    permission_classes = [HasPermissionKey]
    scope = "workspace"

    def perform_create(self, serializer):
        instance = serializer.save()
        self.create_permission_keys(instance, scope="workspace")


@extend_schema_view(
    list=extend_schema(description="Role Permission List"),
    create=extend_schema(description="Role Permission Create"),
    retrieve=extend_schema(description="Role Permission Retrieve"),
    update=extend_schema(description="Role Permission Update"),
    partial_update=extend_schema(description="Role Permission Partial Update"),
    destroy=extend_schema(description="Role Permission Destroy"),
)
class RolePermissionViewSet(viewsets.ModelViewSet):

    queryset = RolePermission.objects.all()
    serializer_class = RolePermissionSerializer
    permission_classes = [IsAdminOrIsAuthenticatedReadOnly]
