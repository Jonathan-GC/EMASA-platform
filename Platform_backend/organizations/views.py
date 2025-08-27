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

from chirpstack.chirpstack_api import sync_tenant_chirpstack_creation

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
            print(f"Se ha creado el grupo: {group_name}")
        
        sync_response = sync_tenant_chirpstack_creation(instance)

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
