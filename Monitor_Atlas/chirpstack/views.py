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

from loguru import logger
from drf_spectacular.utils import extend_schema_view, extend_schema


# Create your views here.


@extend_schema_view(
    list=extend_schema(description="Device Profile List (ChirpStack)"),
    create=extend_schema(description="Device Profile Create (ChirpStack)"),
    retrieve=extend_schema(description="Device Profile Retrieve (ChirpStack)"),
    update=extend_schema(description="Device Profile Update (ChirpStack)"),
    partial_update=extend_schema(
        description="Device Profile Partial Update (ChirpStack)"
    ),
    destroy=extend_schema(description="Device Profile Destroy (ChirpStack)"),
)
class DeviceProfileViewSet(viewsets.ModelViewSet, PermissionKeyMixin):
    queryset = DeviceProfile.objects.all()
    serializer_class = DeviceProfileSerializer
    permission_classes = [HasPermissionKey]
    scope = "device_profile"

    def perform_create(self, serializer):
        instance = serializer.save()
        self.create_permission_keys(instance, scope="device_profile")

        sync_response = sync_device_profile_create(instance)

        if sync_response is None:
            logger.debug(
                f"No changes made in Chirpstack for device_profile {instance.name}, if this is not expected please check manually or try again"
            )
            return

        if sync_response.status_code != 200:
            logger.error(
                f"Error syncing device_profile {instance.name} with Chirpstack: {sync_response.status_code} {instance.sync_error}"
            )
        else:
            logger.debug(
                f"Synchronized device_profile {instance.cs_device_profile_id} - {instance.name} with Chirpstack"
            )

    def perform_update(self, serializer):
        instance = serializer.save()

        sync_response = sync_device_profile_update(instance)

        if sync_response is None:
            logger.debug(
                f"No changes made in Chirpstack for device_profile {instance.name}, if this is not expected please check manually or try again"
            )
            return

        if sync_response.status_code != 200:
            logger.error(
                f"Error syncing device_profile {instance.name} with Chirpstack: {sync_response.status_code} {instance.sync_error}"
            )
        else:
            logger.debug(
                f"Synchronized device_profile {instance.cs_device_profile_id} - {instance.name} with Chirpstack"
            )

    def perform_destroy(self, instance):
        sync_response = sync_device_profile_destroy(instance)

        if sync_response is None:
            logger.debug(
                f"No changes made in Chirpstack for device_profile {instance.name}, if this is not expected please check manually or try again"
            )
            # proceed to delete locally

        elif sync_response.status_code != 200:
            logger.error(
                f"Error deleting device_profile {instance.name} from Chirpstack: {sync_response.status_code} {instance.sync_error}"
            )
        else:
            logger.debug(
                f"Synchronized deletion of device_profile {instance.cs_device_profile_id} - {instance.name} with Chirpstack"
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


@extend_schema_view(
    list=extend_schema(description="(Unused) Device Profile Template List"),
    create=extend_schema(description="(Unused) Device Profile Template Create"),
    retrieve=extend_schema(description="(Unused) Device Profile Template Retrieve"),
    update=extend_schema(description="(Unused) Device Profile Template Update"),
    partial_update=extend_schema(
        description="(Unused) Device Profile Template Partial Update"
    ),
    destroy=extend_schema(description="(Unused) Device Profile Template Destroy"),
)
class DeviceProfileTemplateViewSet(viewsets.ModelViewSet, PermissionKeyMixin):
    queryset = DeviceProfileTemplate.objects.all()
    serializer_class = DeviceProfileTemplateSerializer
    permission_classes = [HasPermissionKey]
    scope = "device_profile_template"

    def perform_create(self, serializer):
        instance = serializer.save()
        self.create_permission_keys(instance, scope="device_profile_template")


@extend_schema_view(
    list=extend_schema(description="Api User List (ChirpStack)"),
    create=extend_schema(description="Api User Create (ChirpStack)"),
    retrieve=extend_schema(description="Api User Retrieve (ChirpStack)"),
    update=extend_schema(description="Api User Update (ChirpStack)"),
    partial_update=extend_schema(description="Api User Partial Update (ChirpStack)"),
    destroy=extend_schema(description="Api User Destroy (ChirpStack)"),
)
class ApiUserViewSet(viewsets.ModelViewSet, PermissionKeyMixin):
    queryset = ApiUser.objects.all()
    serializer_class = ApiUserSerializer
    permission_classes = [HasPermissionKey]
    scope = "api_user"

    def perform_create(self, serializer):
        instance = serializer.save()
        self.create_permission_keys(instance, scope="api_user")

        sync_response = sync_api_user_create(instance)

        if sync_response is None:
            logger.debug(
                f"No changes made in chirpstack for api_user {instance.email}, if this is not expected please check the sync_error field"
            )
            return

        if sync_response.status_code != 200:
            logger.error(
                f"Error syncing api_user {instance.email} with Chirpstack: {sync_response.status_code} {instance.sync_error}"
            )
        else:
            logger.debug(
                f"Synchronized api_user {instance.cs_user_id} - {instance.email} with Chirpstack"
            )

    def perform_update(self, serializer):
        instance = serializer.save()

        sync_response = sync_api_user_update(instance)

        if sync_response is None:
            logger.debug(
                f"No changes made in chirpstack for api_user {instance.email}, if this is not expected please check the sync_error field"
            )
            return

        if sync_response.status_code != 200:
            logger.error(
                f"Error syncing api_user {instance.email} with Chirpstack: {sync_response.status_code} {instance.sync_error}"
            )
        else:
            logger.debug(
                f"Synchronized api_user {instance.cs_user_id} - {instance.email} with Chirpstack"
            )

    def perform_destroy(self, instance):
        sync_response = sync_api_user_destroy(instance)

        if sync_response is None:
            logger.debug(
                f"No changes made in chirpstack for api_user {instance.email}, if this is not expected please check the sync_error field"
            )
            return

        if sync_response.status_code != 200:
            logger.error(
                f"Error deleting api_user {instance.email} from Chirpstack: {sync_response.status_code} {instance.sync_error}"
            )
        else:
            logger.debug(
                f"Synchronized deletion of api_user {instance.cs_user_id} - {instance.email} with Chirpstack"
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
