from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied, ValidationError

from .permissions import HasPermission

from .serializers import (
    RoleSerializer,
    WorkspaceMembershipSerializer,
)
from .models import Role, WorkspaceMembership

from drf_spectacular.utils import extend_schema_view, extend_schema
from .helpers import (
    assign_new_role_base_permissions,
    assign_created_instance_permissions,
    get_assignable_permissions,
    bulk_assign_permissions,
)

from django.contrib.auth.models import Group
from rest_framework.decorators import action
from rest_framework.response import Response
from loguru import logger
from guardian.shortcuts import get_objects_for_user


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
class RoleViewSet(viewsets.ModelViewSet):

    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [HasPermission]
    scope = "role"

    def get_queryset(self):
        user = self.request.user
        user_tenant = user.tenant

        if user.is_superuser:
            return Role.objects.all()
        else:
            return get_objects_for_user(user, "roles.view_role", Role).filter(
                workspace__tenant=user_tenant
            )

    def perform_create(self, serializer):
        user = self.request.user
        user_tenant = user.tenant

        workspace = serializer.validated_data.get("workspace")
        if workspace is None:
            raise ValidationError({"workspace": "Workspace is required."})

        role_tenant = workspace.tenant
        if user_tenant != role_tenant and not user.is_superuser:
            raise PermissionDenied(
                "User does not have permission to create role for this tenant"
            )

        instance = serializer.save()

        assign_new_role_base_permissions(instance, user)

        if not instance.group:
            group = Group.objects.create(
                name=f"{instance.id}_{instance.name}_{instance.workspace.tenant.name}"
            )
            instance.group = group
            instance.save()

        logger.debug(
            f"Assigned base role permissions to user {user.username} for role {instance.name}"
        )

    @action(detail=True, methods=["get"])
    def get_assignable_permissions(self, request, pk=None):
        user = request.user
        workspace = self.get_object().workspace
        role = self.get_object()
        permissions = get_assignable_permissions(user, workspace, role)
        return Response({"assignable_permissions": permissions})

    @action(detail=True, methods=["patch"])
    def bulk_assign_permissions(self, request, pk=None):
        role = self.get_object()
        permissions = request.data.get("permissions", {})
        bulk_assign_permissions(permissions, role)
        return Response({"status": "permissions updated"})


@extend_schema_view(
    list=extend_schema(description="Workspace Membership List"),
    create=extend_schema(description="Workspace Membership Create"),
    retrieve=extend_schema(description="Workspace Membership Retrieve"),
    update=extend_schema(description="Workspace Membership Update"),
    partial_update=extend_schema(description="Workspace Membership Partial Update"),
    destroy=extend_schema(description="Workspace Membership Destroy"),
)
class WorkspaceMembershipViewSet(viewsets.ModelViewSet):

    queryset = WorkspaceMembership.objects.all()
    serializer_class = WorkspaceMembershipSerializer
    permission_classes = [HasPermission]
    scope = "workspacemembership"

    def get_queryset(self):
        user = self.request.user
        user_tenant = user.tenant

        if user.is_superuser:
            return WorkspaceMembership.objects.all()
        else:
            return get_objects_for_user(
                user, "roles.view_workspacemembership", WorkspaceMembership
            ).filter(workspace__tenant=user_tenant)

    def perform_create(self, serializer):
        instance = serializer.save()
        assign_created_instance_permissions(instance, self.request.user)

        role = instance.role
        group = role.group
        user = instance.user

        # Assign role group to user
        if group:
            user.groups.add(group)
            user.save()
            logger.debug(
                f"Added user {user.username} to group {group.name} for role {role.name}"
            )
