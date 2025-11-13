from rest_framework import viewsets

from .permissions import HasPermission

from .serializers import (
    RoleSerializer,
    WorkspaceMembershipSerializer,
)
from .models import Role, WorkspaceMembership

from drf_spectacular.utils import extend_schema_view, extend_schema
from .helpers import assign_new_role_base_permissions

from django.contrib.auth.models import Group

from loguru import logger


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

    def perform_create(self, serializer):
        instance = serializer.save()
        user = self.request.user
        user_tenant = user.tenant
        role_tenant = instance.workspace.tenant
        if user_tenant != role_tenant:
            raise PermissionError(
                "User does not have permission to create role for this tenant"
            )
        assign_new_role_base_permissions(instance, user)
        logger.debug(
            f"Assigned base role permissions to user {user.username} for role {instance.name}"
        )


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
    scope = "workspace"

    def perform_create(self, serializer):
        instance = serializer.save()

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
