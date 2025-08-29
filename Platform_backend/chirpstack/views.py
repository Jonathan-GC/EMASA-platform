from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import DeviceProfile, DeviceProfileTemplate, ApiUser
from .serializers import (
    DeviceProfileSerializer,
    DeviceProfileTemplateSerializer,
    ApiUserSerializer,
)

from roles.permissions import HasPermissionKey, IsAdminOrIsAuthenticatedReadOnly
from roles.mixins import PermissionKeyMixin
from roles.models import PermissionKey
from roles.serializers import PermissionKeySerializer

from chirpstack.chirpstack_api import (
    sync_api_user_create,
    sync_api_user_destroy,
    sync_api_user_update,
    sync_api_user_get,
    sync_device_profile_create,
    sync_device_profile_destroy,
    sync_device_profile_get,
    sync_device_profile_update,
)

import logging

# Create your views here.


class DeviceProfileViewSet(viewsets.ModelViewSet, PermissionKeyMixin):
    queryset = DeviceProfile.objects.all()
    serializer_class = DeviceProfileSerializer
    permission_classes = [HasPermissionKey]
    scope = "device_profile"

    def perform_create(self, serializer):
        instance = serializer.save()
        self.create_permission_keys(instance, scope="device_profile")

        sync_response = sync_device_profile_create(instance)

        if sync_response.status_code != 200:
            logging.error(
                f"Error al sincronizar el device_profile {instance.name} con Chirpstack: {sync_response.status_code} {instance.sync_error}"
            )
        else:
            logging.info(
                f"Se ha sincronizado el device_profile {instance.cs_device_profile_id} - {instance.name} con Chirpstack"
            )

    def perform_update(self, serializer):
        instance = serializer.save()

        sync_response = sync_device_profile_update(instance)

        if sync_response.status_code != 200:
            logging.error(
                f"Error al sincronizar el device_profile {instance.name} con Chirpstack: {sync_response.status_code} {instance.sync_error}"
            )
        else:
            logging.info(
                f"Se ha sincronizado el device_profile {instance.cs_device_profile_id} - {instance.name} con Chirpstack"
            )

    def perform_destroy(self, instance):
        sync_response = sync_device_profile_destroy(instance)

        if sync_response.status_code != 200:
            logging.error(
                f"Error al eliminar el device_profile {instance.name} con Chirpstack: {sync_response.status_code} {instance.sync_error}"
            )
        else:
            logging.info(
                f"Se ha sincronizado el device_profile {instance.cs_device_profile_id} - {instance.name} con Chirpstack"
            )

        instance.delete()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        sync_device_profile_get(instance)
        instance.refresh_from_db()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        for device_profile in queryset:
            sync_device_profile_get(device_profile)
            device_profile.refresh_from_db()

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAdminOrIsAuthenticatedReadOnly],
    )
    def regenerate_permission_keys(self, request, pk=None):
        instance = self.get_object()
        scope = "device_profile"

        self.create_permission_keys(instance, scope)

        permission_keys = PermissionKey.objects.filter(
            **{self.scope_field_map[scope]: instance}
        )
        serializer = PermissionKeySerializer(permission_keys, many=True)

        return Response(serializer.data)


class DeviceProfileTemplateViewSet(viewsets.ModelViewSet, PermissionKeyMixin):
    queryset = DeviceProfileTemplate.objects.all()
    serializer_class = DeviceProfileTemplateSerializer
    permission_classes = [HasPermissionKey]
    scope = "device_profile_template"

    def perform_create(self, serializer):
        instance = serializer.save()
        self.create_permission_keys(instance, scope="device_profile_template")

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAdminOrIsAuthenticatedReadOnly],
    )
    def regenerate_permission_keys(self, request, pk=None):
        instance = self.get_object()
        scope = "device_profile_template"

        self.create_permission_keys(instance, scope)

        permission_keys = PermissionKey.objects.filter(
            **{self.scope_field_map[scope]: instance}
        )
        serializer = PermissionKeySerializer(permission_keys, many=True)

        return Response(serializer.data)


class ApiUserViewSet(viewsets.ModelViewSet, PermissionKeyMixin):
    queryset = ApiUser.objects.all()
    serializer_class = ApiUserSerializer
    permission_classes = [HasPermissionKey]
    scope = "api_user"

    def perform_create(self, serializer):
        instance = serializer.save()
        self.create_permission_keys(instance, scope="api_user")

        sync_response = sync_api_user_create(instance)

        if sync_response.status_code != 200:
            logging.error(
                f"Error al sincronizar el api_user {instance.email} con Chirpstack: {sync_response.status_code} {instance.sync_error}"
            )
        else:
            logging.info(
                f"Se ha sincronizado el api_user {instance.cs_user_id} - {instance.email} con Chirpstack"
            )

    def perform_update(self, serializer):
        instance = serializer.save()

        sync_response = sync_api_user_update(instance)

        if sync_response.status_code != 200:
            logging.error(
                f"Error al sincronizar el api_user {instance.email} con Chirpstack: {sync_response.status_code} {instance.sync_error}"
            )
        else:
            logging.info(
                f"Se ha sincronizado el api_user {instance.cs_user_id} - {instance.email} con Chirpstack"
            )

    def perform_destroy(self, instance):
        sync_response = sync_api_user_destroy(instance)

        if sync_response.status_code != 200:
            logging.error(
                f"Error al eliminar el api_user {instance.email} con Chirpstack: {sync_response.status_code} {instance.sync_error}"
            )
        else:
            logging.info(
                f"Se ha sincronizado el api_user {instance.cs_user_id} - {instance.email} con Chirpstack"
            )

        instance.delete()

    def retrieve(self, request, *args, **kwargs):

        instance = self.get_object()

        sync_api_user_get(instance)
        instance.refresh_from_db()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        for api_user in queryset:
            sync_api_user_get(api_user)
            api_user.refresh_from_db()

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAdminOrIsAuthenticatedReadOnly],
    )
    def regenerate_permission_keys(self, request, pk=None):
        instance = self.get_object()
        scope = "api_user"

        self.create_permission_keys(instance, scope)

        permission_keys = PermissionKey.objects.filter(
            **{self.scope_field_map[scope]: instance}
        )
        serializer = PermissionKeySerializer(permission_keys, many=True)

        return Response(serializer.data)
