from rest_framework import viewsets
from rest_framework.response import Response
from django.contrib.auth.models import Group

from .models import Workspace, Tenant, Subscription
from .serializers import WorkspaceSerializer, TenantSerializer, SubscriptionSerializer

from roles.permissions import HasPermissionKey
from roles.mixins import PermissionKeyMixin

from chirpstack.chirpstack_api import (
    sync_tenant_get,
    sync_tenant_create,
    sync_tenant_destroy,
    sync_tenant_update,
)

from loguru import logger
from drf_spectacular.utils import extend_schema_view, extend_schema


@extend_schema_view(
    list=extend_schema(description="Workspace List"),
    create=extend_schema(description="Workspace Create"),
    retrieve=extend_schema(description="Workspace Retrieve"),
    update=extend_schema(description="Workspace Update"),
    partial_update=extend_schema(description="Workspace Partial Update"),
    destroy=extend_schema(description="Workspace Destroy"),
)
class WorkspaceViewSet(viewsets.ModelViewSet, PermissionKeyMixin):
    queryset = Workspace.objects.all()
    serializer_class = WorkspaceSerializer
    permission_classes = [HasPermissionKey]
    scope = "workspace"

    def perform_create(self, serializer):
        instance = serializer.save()
        self.create_permission_keys(instance, scope="workspace")


@extend_schema_view(
    list=extend_schema(description="Tenant List"),
    create=extend_schema(description="Tenant Create"),
    retrieve=extend_schema(description="Tenant Retrieve"),
    update=extend_schema(description="Tenant Update"),
    partial_update=extend_schema(description="Tenant Partial Update"),
    destroy=extend_schema(description="Tenant Destroy"),
)
class TenantViewSet(viewsets.ModelViewSet, PermissionKeyMixin):
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    permission_classes = [HasPermissionKey]
    scope = "tenant"

    def perform_create(self, serializer):
        instance = serializer.save()
        self.create_permission_keys(instance, scope="tenant")

        group_name = instance.group
        group, created = Group.objects.get_or_create(name=group_name)

        if created:
            logger.debug(f"Grupo {group_name} creado exitosamente")

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


@extend_schema_view(
    list=extend_schema(description="Subscription List"),
    create=extend_schema(description="Subscription Create"),
    retrieve=extend_schema(description="Subscription Retrieve"),
    update=extend_schema(description="Subscription Update"),
    partial_update=extend_schema(description="Subscription Partial Update"),
    destroy=extend_schema(description="Subscription Destroy"),
)
class SubscriptionViewSet(viewsets.ModelViewSet, PermissionKeyMixin):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    permission_classes = [HasPermissionKey]
    scope = "subscription"

    def perform_create(self, serializer):
        instance = serializer.save()
        self.create_permission_keys(instance, scope="subscription")
