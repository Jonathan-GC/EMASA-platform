from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .serializers import (
    GatewaySerializer,
    MachineSerializer,
    TypeSerializer,
    DeviceSerializer,
    ApplicationSerializer,
    LocationSerializer,
)
from .models import Gateway, Machine, Type, Device, Application, Location, Activation

from roles.permissions import HasPermissionKey, IsAdminOrIsAuthenticatedReadOnly
from roles.mixins import PermissionKeyMixin
from roles.models import PermissionKey
from roles.serializers import PermissionKeySerializer

from chirpstack.chirpstack_api import (
    sync_gateway_create,
    sync_gateway_get,
    sync_gateway_update,
    sync_gateway_destroy,
    sync_application_destroy,
    sync_application_update,
    sync_application_create,
    sync_application_get,
    sync_device_create,
    sync_device_update,
    sync_device_destroy,
    sync_device_get,
    activate_device,
    deactivate_device,
    device_activation_status,
)
from rest_framework import status

import logging

from drf_spectacular.utils import extend_schema_view, extend_schema


@extend_schema_view(
    list=extend_schema(description="Gateway List (ChirpStack)"),
    create=extend_schema(description="Gateway Create (ChirpStack)"),
    retrieve=extend_schema(description="Gateway Retrieve (ChirpStack)"),
    update=extend_schema(description="Gateway Update (ChirpStack)"),
    partial_update=extend_schema(description="Gateway Partial Update (ChirpStack)"),
    destroy=extend_schema(description="Gateway Destroy (ChirpStack)"),
)
class GatewayViewSet(viewsets.ModelViewSet, PermissionKeyMixin):
    queryset = Gateway.objects.all()
    serializer_class = GatewaySerializer
    permission_classes = [HasPermissionKey]
    scope = "gateway"

    def perform_create(self, serializer):
        instance = serializer.save()
        self.create_permission_keys(instance, scope="gateway")

        sync_response = sync_gateway_create(instance)

        if sync_response.status_code != 200:
            logging.error(
                f"Error al crear el gateway {instance.name} con Chirpstack: {sync_response.status_code} {instance.sync_error}"
            )
        else:
            logging.info(
                f"Se ha sincronizado el gateway {instance.cs_gateway_id} - {instance.name} con Chirpstack"
            )

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve a gateway and sync it with Chirpstack before returning the response.

        """
        instance = self.get_object()

        sync_gateway_get(instance)
        instance.refresh_from_db()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        """
        List a queryset of gateways and sync each one with Chirpstack before
        returning the response.

        """

        queryset = self.filter_queryset(self.get_queryset())

        for gateway in queryset:
            sync_gateway_get(gateway)
            gateway.refresh_from_db()

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def perform_update(self, serializer):
        """
        Update a gateway and sync it with Chirpstack.

        Args:
            serializer: a GatewaySerializer instance

        """
        instance = serializer.save()

        sync_response = sync_gateway_update(instance)

        if sync_response.status_code != 200:
            logging.error(
                f"Error al actualizar el gateway {instance.name} con Chirpstack: {sync_response.status_code} {instance.sync_error}"
            )
        else:
            logging.info(
                f"Se ha sincronizado el gateway {instance.cs_gateway_id} - {instance.name} con Chirpstack"
            )

    def perform_destroy(self, instance):
        sync_response = sync_gateway_destroy(instance, request=self.request)

        if sync_response.status_code != 200:
            logging.error(
                f"Error al eliminar el gateway {instance.name} con Chirpstack: {sync_response.status_code} {instance.sync_error}"
            )
        else:
            logging.info(
                f"Se ha sincronizado el gateway {instance.cs_gateway_id} - {instance.name} con Chirpstack"
            )

        instance.delete()


@extend_schema_view(
    list=extend_schema(description="Machine List"),
    create=extend_schema(description="Machine Create"),
    retrieve=extend_schema(description="Machine Retrieve"),
    update=extend_schema(description="Machine Update"),
    partial_update=extend_schema(description="Machine Partial Update"),
    destroy=extend_schema(description="Machine Destroy"),
    set_machine_image=extend_schema(description="Set Machine Image"),
)
class MachineViewSet(viewsets.ModelViewSet, PermissionKeyMixin):
    queryset = Machine.objects.all()
    serializer_class = MachineSerializer
    permission_classes = [HasPermissionKey]
    scope = "machine"

    def perform_create(self, serializer):
        instance = serializer.save()
        self.create_permission_keys(instance, scope="machine")

    @action(detail=True, methods=["patch"], permission_classes=[HasPermissionKey])
    def set_machine_image(self, request, pk=None):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(description="Type List"),
    create=extend_schema(description="Type Create"),
    retrieve=extend_schema(description="Type Retrieve"),
    update=extend_schema(description="Type Update"),
    partial_update=extend_schema(description="Type Partial Update"),
    destroy=extend_schema(description="Type Destroy"),
    set_type_image=extend_schema(description="Set Type Image (icon)"),
)
class TypeViewSet(viewsets.ModelViewSet, PermissionKeyMixin):
    queryset = Type.objects.all()
    serializer_class = TypeSerializer
    permission_classes = [HasPermissionKey]
    scope = "type"

    def perform_create(self, serializer):
        instance = serializer.save()
        self.create_permission_keys(instance, scope="type")

    @action(detail=True, methods=["patch"], permission_classes=[HasPermissionKey])
    def set_type_image(self, request, pk=None):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(description="Device List (ChirpStack)"),
    create=extend_schema(description="Device Create (ChirpStack)"),
    retrieve=extend_schema(description="Device Retrieve (ChirpStack)"),
    update=extend_schema(description="Device Update (ChirpStack)"),
    partial_update=extend_schema(description="Device Partial Update (ChirpStack)"),
    destroy=extend_schema(description="Device Destroy (ChirpStack)"),
    set_activation=extend_schema(description="Set Device Activation Data"),
    activate=extend_schema(description="Activate Device"),
    deactivate=extend_schema(description="Deactivate Device"),
)
class DeviceViewSet(viewsets.ModelViewSet, PermissionKeyMixin):
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer
    permission_classes = [HasPermissionKey]
    scope = "device"

    def perform_create(self, serializer):
        instance = serializer.save()
        self.create_permission_keys(instance, scope="device")

        sync_response = sync_device_create(instance)

        if sync_response.status_code != 200:
            logging.error(
                f"Error al crear el dispositivo {instance.name} con Chirpstack: {sync_response.status_code} {instance.sync_error}"
            )
        else:
            logging.info(
                f"Se ha sincronizado el dispositivo {instance.dev_eui} - {instance.name} con Chirpstack"
            )

    def perform_update(self, serializer):
        instance = serializer.save()

        sync_response = sync_device_update(instance)

        if sync_response.status_code != 200:
            logging.error(
                f"Error al sincronizar el dispositivo {instance.name} con Chirpstack: {sync_response.status_code} {instance.sync_error}"
            )
        else:
            logging.info(
                f"Se ha sincronizado el dispositivo {instance.dev_eui} - {instance.name} con Chirpstack"
            )

    def perform_destroy(self, instance):
        sync_response = sync_device_destroy(instance)

        if sync_response.status_code != 200:
            logging.error(
                f"Error al eliminar el dispositivo {instance.name} con Chirpstack: {sync_response.status_code} {instance.sync_error}"
            )
        else:
            logging.info(
                f"Se ha sincronizado el dispositivo {instance.dev_eui} - {instance.name} con Chirpstack"
            )

        instance.delete()

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        for device in queryset:
            sync_device_get(device)
            device.refresh_from_db()

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        sync_device_get(instance)
        instance.refresh_from_db()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[HasPermissionKey],
        scope="device",
    )
    def set_activation(self, request, pk=None):
        """
        "aFCntDown": 0,
        "appSKey": "53C020841486263981FA77355D278762",
        "devAddr": "260CB229",
        "fCntUp": 0,
        "fNwkSIntKey": "4978CB8E7FFBD46BC570FE11F17FA56E",
        "nFCntDown": 0,
        "nwkSEncKey": "4978CB8E7FFBD46BC570FE11F17FA56E"
        """

        device = self.get_object()

        data = request.data
        required_fields = [
            "afcntdown",
            "app_s_key",
            "dev_addr",
            "f_cnt_up",
            "f_nwk_s_int_key",
            "n_f_cnt_down",
            "nwk_s_enc_key",
            "s_nwk_s_int_key",
        ]
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return Response(
                {"message": f"Missing required fields: {', '.join(missing_fields)}"},
                status=400,
            )
        try:
            activation = Activation.objects.create(
                afcntdown=data["afcntdown"],
                app_s_key=data["app_s_key"],
                dev_addr=data["dev_addr"],
                f_cnt_up=data["f_cnt_up"],
                f_nwk_s_int_key=data["f_nwk_s_int_key"],
                n_f_cnt_down=data["n_f_cnt_down"],
                nwk_s_enc_key=data["nwk_s_enc_key"],
                s_nwk_s_int_key=data["s_nwk_s_int_key"],
            )
            device.activation = activation
            device.save()
            serializer = self.get_serializer(device)
            return Response(serializer.data)
        except Exception as e:
            logging.error(
                f"Error setting activation for device {device.name}: {str(e)}"
            )
            return Response(
                {"message": f"Error setting activation: {str(e)}"},
                status=500,
            )

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[HasPermissionKey],
        scope="device",
    )
    def activate(self, request, pk=None):
        device = self.get_object()

        if not device.activation:
            return Response(
                {"message": "Device has no activation data"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if device_activation_status(device):
            return Response(
                {"message": "Device is already active"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            sync_response = activate_device(device)

            if sync_response.status_code != 200:
                device.is_active = False
                device.sync_error = sync_response.text
                device.save(update_fields=["is_active", "sync_error"])
                logging.error(
                    f"Activation failed for {device.name}: {sync_response.status_code} {sync_response.text}"
                )
                return Response(
                    {
                        "message": "Error activating device",
                        "details": sync_response.text,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            device.is_active = True
            device.save(update_fields=["is_active"])
            logging.info(f"Device {device.dev_eui} - {device.name} activated")

            serializer = self.get_serializer(device)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logging.exception(f"Unexpected error activating device {device.name}")
            return Response(
                {"message": "Unexpected error activating device", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[HasPermissionKey],
        scope="device",
    )
    def deactivate(self, request, pk=None):
        instance = self.get_object()
        sync_response = deactivate_device(instance)

        if sync_response.status_code != 200:
            logging.error(
                f"Error al desactivar el dispositivo {instance.name} con Chirpstack: {sync_response.status_code} {instance.sync_error}"
            )
            return Response(
                {
                    "message": f"Error al desactivar el dispositivo {sync_response.status_code} {instance.sync_error}"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:
            logging.info(
                f"Se ha desactivado el dispositivo {instance.dev_eui} - {instance.name}"
            )

        return Response({"message": "Device deactivated"})

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAdminOrIsAuthenticatedReadOnly],
    )
    def regenerate_permission_keys(self, request, pk=None):
        instance = self.get_object()
        scope = "device"

        self.create_permission_keys(instance, scope)

        permission_keys = PermissionKey.objects.filter(
            **{self.scope_field_map[scope]: instance}
        )
        serializer = PermissionKeySerializer(permission_keys, many=True)

        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(description="Application List (ChirpStack)"),
    create=extend_schema(description="Application Create (ChirpStack)"),
    retrieve=extend_schema(description="Application Retrieve (ChirpStack)"),
    update=extend_schema(description="Application Update (ChirpStack)"),
    partial_update=extend_schema(description="Application Partial Update (ChirpStack)"),
    destroy=extend_schema(description="Application Destroy (ChirpStack)"),
)
class ApplicationViewSet(viewsets.ModelViewSet, PermissionKeyMixin):
    queryset = Application.objects.all()
    serializer_class = ApplicationSerializer
    permission_classes = [HasPermissionKey]
    scope = "application"

    def perform_create(self, serializer):
        instance = serializer.save()
        self.create_permission_keys(instance, scope="application")

        sync_response = sync_application_create(instance)

        if sync_response.status_code != 200:
            logging.error(
                f"Error al crear la aplicación {instance.name} con Chirpstack: {sync_response.status_code} {instance.sync_error}"
            )
        else:
            logging.info(
                f"Se ha sincronizado la aplicación {instance.cs_application_id} - {instance.name} con Chirpstack"
            )

    def perform_destroy(self, instance):
        sync_response = sync_application_destroy(instance)

        if sync_response.status_code != 200:
            logging.error(
                f"Error al eliminar la aplicación {instance.name} con Chirpstack: {sync_response.status_code} {instance.sync_error}"
            )
        else:
            logging.info(
                f"Se ha sincronizado la aplicación {instance.cs_application_id} - {instance.name} con Chirpstack"
            )

        instance.delete()

    def perform_update(self, serializer):
        instance = serializer.save()

        sync_response = sync_application_update(instance)

        if sync_response.status_code != 200:
            logging.error(
                f"Error al sincronizar la aplicación {instance.name} con Chirpstack: {sync_response.status_code} {instance.sync_error}"
            )
        else:
            logging.info(
                f"Se ha sincronizado la aplicación {instance.cs_application_id} - {instance.name} con Chirpstack"
            )

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        for application in queryset:
            logging.info(f"Syncing application {application.name}")
            sync_application_get(application)

            application.refresh_from_db()

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        sync_application_get(instance)
        instance.refresh_from_db()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(description="Location List"),
    create=extend_schema(description="Location Create"),
    retrieve=extend_schema(description="Location Retrieve"),
    update=extend_schema(description="Location Update"),
    partial_update=extend_schema(description="Location Partial Update"),
    destroy=extend_schema(description="Location Destroy"),
)
class LocationViewSet(viewsets.ModelViewSet, PermissionKeyMixin):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    permission_classes = [HasPermissionKey]
    scope = "location"

    def perform_create(self, serializer):
        instance = serializer.save()
        self.create_permission_keys(instance, scope="location")
