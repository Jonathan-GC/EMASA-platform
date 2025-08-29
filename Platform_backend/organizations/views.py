from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.models import Group

from .models import Workspace, Tenant, Subscription
from .serializers import WorkspaceSerializer, TenantSerializer, SubscriptionSerializer

from roles.permissions import IsAdminOrIsAuthenticatedReadOnly, HasPermissionKey
from roles.mixins import PermissionKeyMixin
from roles.models import PermissionKey
from roles.serializers import PermissionKeySerializer

from chirpstack.chirpstack_api import sync_tenant_chirpstack, sync_tenant_get

import logging

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
            logging.info(f"Grupo {group_name} creado exitosamente")
        
        sync_response = sync_tenant_chirpstack(instance, request=self.request)

        if sync_response.status_code != 200:
            logging.error(f"Error al sincronizar el tenant {instance.name} con Chirpstack: {sync_response.status_code}")
        else:
            logging.info(f"Se ha sincronizado el tenant {instance.name} con Chirpstack")
    
    def perform_update(self, serializer):
        instance = serializer.save()
        
        sync_response = sync_tenant_chirpstack(instance, request=self.request)

        if sync_response.status_code != 200:
            logging.error(f"Error al sincronizar el tenant {instance.name} con Chirpstack: {sync_response.status_code}")
        else:
            logging.info(f"Se ha sincronizado el tenant {instance.name} con Chirpstack")
    
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
            if sync_response.status_code != 200:
                logging.error(f"Error al sincronizar el tenant {tenant.name} con Chirpstack: {sync_response.status_code}")
            else:
                logging.info(f"Se ha sincronizado el tenant {tenant.name} con Chirpstack")
            tenant.refresh_from_db()

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def perform_destroy(self, instance):
        sync_response = sync_tenant_chirpstack(instance, request=self.request)

        if sync_response.status_code != 200:
            logging.error(f"Error al sincronizar el tenant {instance.name} con Chirpstack: {sync_response.status_code}")
        else:
            logging.info(f"Se ha sincronizado el tenant {instance.name} con Chirpstack")


    @action(detail=True, methods=["post"], permission_classes=[IsAdminOrIsAuthenticatedReadOnly])
    def regenerate_permission_keys(self, request, pk=None):
        instance = self.get_object()
        scope = "tenant"

        self.create_permission_keys(instance, scope)

        permission_keys = PermissionKey.objects.filter(
            **{self.scope_field_map[scope]: instance}
        )
        serializer = PermissionKeySerializer(permission_keys, many=True)
        
        return Response(serializer.data)


class SubscriptionViewSet(viewsets.ModelViewSet, PermissionKeyMixin):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    permission_classes = [HasPermissionKey]
    scope = "subscription"

    def perform_create(self, serializer):
        instance = serializer.save()
        self.create_permission_keys(instance, scope="subscription")

    @action(detail=True, methods=["post"], permission_classes=[IsAdminOrIsAuthenticatedReadOnly])
    def regenerate_permission_keys(self, request, pk=None):
        instance = self.get_object()
        scope = "subscription"

        self.create_permission_keys(instance, scope)

        permission_keys = PermissionKey.objects.filter(
            **{self.scope_field_map[scope]: instance}
        )
        serializer = PermissionKeySerializer(permission_keys, many=True)
        
        return Response(serializer.data)
