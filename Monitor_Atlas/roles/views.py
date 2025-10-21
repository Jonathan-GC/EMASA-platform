from rest_framework import viewsets

from .permissions import HasPermission

from .serializers import (
    RoleSerializer,
    WorkspaceMembershipSerializer,
)
from .models import Role, WorkspaceMembership
from .helpers import (
    assign_workspace_permissions,
    assign_role_permissions,
    remove_workspace_permissions,
)

from guardian.shortcuts import get_objects_for_user
from organizations.models import Workspace

from drf_spectacular.utils import extend_schema_view, extend_schema
from loguru import logger


@extend_schema_view(
    list=extend_schema(description="Role List"),
    create=extend_schema(description="Role Create"),
    retrieve=extend_schema(description="Role Retrieve"),
    update=extend_schema(description="Role Update"),
    partial_update=extend_schema(description="Role Partial Update"),
    destroy=extend_schema(description="Role Destroy"),
)
class RoleViewSet(viewsets.ModelViewSet):

    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [HasPermission]
    scope = "role"

    def get_queryset(self):
        """Filter roles by user's workspace"""

        user = self.request.user
        if user.is_superuser:
            return Role.objects.all()

        workspaces = get_objects_for_user(
            user,
            "organizations.view_workspace",
            klass=Workspace,
        )

        return Role.objects.filter(workspace__in=workspaces)


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

    def perform_create(self, serializer):
        """Assign permissions upon creating a workspace membership."""
        instance = serializer.save()

        if instance.workspace.tenant.is_super_tenant:
            instance.user.is_emasa_user = True
            instance.user.save(update_fields=["is_emasa_user"])

        assign_workspace_permissions(instance.user, instance.workspace, instance.role)
        assign_role_permissions(instance.user, instance.role, instance.workspace)
        logger.debug(
            f"Created WorkspaceMembership and assigned permissions: {instance}"
        )

    def perform_update(self, serializer):
        """Update permissions upon updating a workspace membership."""
        old_instance = self.get_object()
        instance = serializer.save()
        if old_instance.role != instance.role:
            # Role has changed, update permissions
            remove_workspace_permissions(
                instance.user, instance.workspace, old_instance.role
            )
            assign_workspace_permissions(
                instance.user, instance.workspace, instance.role
            )
            assign_role_permissions(instance.user, instance.role, instance.workspace)
            logger.debug(
                f"Updated WorkspaceMembership and updated permissions: {instance}"
            )

    def perform_destroy(self, instance):
        """Remove permissions upon deleting a workspace membership."""
        remove_workspace_permissions(instance.user, instance.workspace, instance.role)
        instance.delete()
        logger.debug(f"Deleted WorkspaceMembership and removed permissions: {instance}")
