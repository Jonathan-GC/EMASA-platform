from rest_framework import viewsets
from rest_framework.response import Response
from django.contrib.auth.models import Group

from .models import Workspace, Tenant, Subscription
from .serializers import WorkspaceSerializer, TenantSerializer, SubscriptionSerializer

from roles.permissions import HasPermission

from chirpstack.chirpstack_api import (
    sync_tenant_get,
    sync_tenant_create,
    sync_tenant_destroy,
    sync_tenant_update,
)

from loguru import logger
from drf_spectacular.utils import extend_schema_view, extend_schema

from roles.helpers import (
    assign_new_tenant_base_permissions,
    assign_new_workspace_base_permissions,
)

from rest_framework.decorators import action


@extend_schema_view(
    list=extend_schema(description="Workspace List"),
    create=extend_schema(description="Workspace Create"),
    retrieve=extend_schema(description="Workspace Retrieve"),
    update=extend_schema(description="Workspace Update"),
    partial_update=extend_schema(description="Workspace Partial Update"),
    destroy=extend_schema(description="Workspace Destroy"),
)
class WorkspaceViewSet(viewsets.ModelViewSet):
    queryset = Workspace.objects.all()
    serializer_class = WorkspaceSerializer
    permission_classes = [HasPermission]
    scope = "workspace"

    def perform_create(self, serializer):
        instance = serializer.save()
        user = self.request.user
        user_tenant = user.tenant
        workspace_tenant = instance.tenant
        if user_tenant != workspace_tenant:
            logger.warning(
                f"User tenant {user_tenant} does not match workspace tenant {workspace_tenant}"
            )
            raise PermissionError(
                "User does not have permission to create workspace for this tenant"
            )
        assign_new_workspace_base_permissions(instance, user)
        logger.debug(
            f"Assigned base workspace permissions to user {user.username} for workspace {instance.name}"
        )


@extend_schema_view(
    list=extend_schema(description="Tenant List"),
    create=extend_schema(description="Tenant Create"),
    retrieve=extend_schema(description="Tenant Retrieve"),
    update=extend_schema(description="Tenant Update"),
    partial_update=extend_schema(description="Tenant Partial Update"),
    destroy=extend_schema(description="Tenant Destroy"),
    get_tenant_by_cs_id=extend_schema(description="Get Tenant by CS ID"),
)
class TenantViewSet(viewsets.ModelViewSet):
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    permission_classes = [HasPermission]
    scope = "tenant"

    def perform_create(self, serializer):
        instance = serializer.save()
        user = self.request.user

        user.tenant = instance
        user.save()

        assign_new_tenant_base_permissions(instance, user)

        sync_response = sync_tenant_create(instance)

        if sync_response is None:
            logger.error(
                f"No se han realizado cambios en Chirpstack, verifique en los logs"
            )
            return

        if sync_response.status_code != 200:
            logger.error(
                f"Error al sincronizar el tenant {instance.name} con Chirpstack: {sync_response.status_code}"
            )
        else:
            logger.debug(f"Se ha sincronizado el tenant {instance.name} con Chirpstack")

    def perform_update(self, serializer):
        instance = serializer.save()

        sync_response = sync_tenant_update(instance)

        if sync_response is None:
            logger.error(
                f"No se han realizado cambios en Chirpstack, verifique en los logs"
            )
            return

        if sync_response.status_code != 200:
            logger.error(
                f"Error al sincronizar el tenant {instance.name} con Chirpstack: {sync_response.status_code}"
            )
        else:
            logger.debug(f"Se ha sincronizado el tenant {instance.name} con Chirpstack")

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        sync_tenant_get(instance)
        instance.refresh_from_db()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        for tenant in queryset:
            sync_response = sync_tenant_get(tenant)
            if sync_response is None:
                logger.error(
                    f"No se han realizado cambios en Chirpstack, verifique en los logs"
                )
                return

            if sync_response.status_code != 200:
                logger.error(
                    f"Error al sincronizar el tenant {tenant.name} con Chirpstack: {sync_response.status_code}"
                )
            else:
                logger.debug(
                    f"Se ha sincronizado el tenant {tenant.name} con Chirpstack"
                )
            tenant.refresh_from_db()

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def perform_destroy(self, instance):
        sync_response = sync_tenant_destroy(instance)

        if sync_response is None:
            logger.error(
                f"No se han realizado cambios en Chirpstack, verifique en los logs"
            )
            return

        if sync_response.status_code != 200:
            logger.error(
                f"Error al sincronizar el tenant {instance.name} con Chirpstack: {sync_response.status_code}"
            )
        else:
            logger.debug(f"Se ha sincronizado el tenant {instance.name} con Chirpstack")

        instance.delete()

    @action(
        detail=False,
        methods=["get"],
        url_path="(?P<cs_tenant_id>[^/.]+)",
        permission_classes=[HasPermission],
        scope="tenant",
    )
    def get_tenant_by_cs_id(self, request, cs_tenant_id=None):
        """
        Custom action to get tenant details by CS tenant ID.
        """
        try:
            tenant = Tenant.objects.filter(cs_tenant_id=cs_tenant_id).first()
            serializer = self.get_serializer(tenant)
            return Response(serializer.data)
        except Tenant.DoesNotExist:
            return Response({"detail": "Tenant not found."}, status=404)


@extend_schema_view(
    list=extend_schema(description="Subscription List"),
    create=extend_schema(description="Subscription Create"),
    retrieve=extend_schema(description="Subscription Retrieve"),
    update=extend_schema(description="Subscription Update"),
    partial_update=extend_schema(description="Subscription Partial Update"),
    destroy=extend_schema(description="Subscription Destroy"),
)
class SubscriptionViewSet(viewsets.ModelViewSet):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    permission_classes = [HasPermission]
    scope = "subscription"

    def perform_create(self, serializer):
        instance = serializer.save()
