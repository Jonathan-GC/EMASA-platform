from .models import (
    Machine,
    Type,
    Device,
    Application,
    Gateway,
    Location,
    Activation,
    Measurements,
    DeviceConsent,
)
from rest_framework import serializers
from organizations.serializers import WorkspaceSerializer
from organizations.models import Workspace


class MachineSerializer(serializers.ModelSerializer):
    workspace = serializers.SerializerMethodField(read_only=True)
    workspace_id = serializers.PrimaryKeyRelatedField(
        queryset=Workspace.objects.all(), write_only=True, source="workspace"
    )

    class Meta:
        model = Machine
        fields = "__all__"

    def get_workspace(self, obj):
        workspace = obj.workspace
        if workspace:
            return {
                "id": workspace.id,
                "name": workspace.name,
                "tenant_id": workspace.tenant.id if workspace.tenant else None,
                "tenant": workspace.tenant.name if workspace.tenant else None,
            }
        return None


class TypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Type
        fields = "__all__"


class DeviceSerializer(serializers.ModelSerializer):
    workspace = serializers.SerializerMethodField(read_only=True)
    workspace_id = serializers.PrimaryKeyRelatedField(
        queryset=Workspace.objects.all(), write_only=True, source="workspace"
    )
    machine_name = serializers.ReadOnlyField(source="machine.name")
    type_name = serializers.ReadOnlyField(source="device_type.name")

    class Meta:
        model = Device
        fields = "__all__"

    def get_workspace(self, obj):
        workspace = obj.workspace
        if workspace:
            return {
                "id": workspace.id,
                "name": workspace.name,
                "tenant_id": workspace.tenant.id if workspace.tenant else None,
                "tenant": workspace.tenant.name if workspace.tenant else None,
            }
        return None


class ApplicationSerializer(serializers.ModelSerializer):
    workspace = serializers.SerializerMethodField(read_only=True)
    workspace_id = serializers.PrimaryKeyRelatedField(
        queryset=Workspace.objects.all(), write_only=True, source="workspace"
    )
    devices_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Application
        fields = "__all__"

    def get_workspace(self, obj):
        workspace = obj.workspace
        if workspace:
            return {
                "id": workspace.id,
                "name": workspace.name,
                "tenant_id": workspace.tenant.id if workspace.tenant else None,
                "tenant": workspace.tenant.name if workspace.tenant else None,
            }
        return None


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = "__all__"


class GatewaySerializer(serializers.ModelSerializer):
    location = LocationSerializer(read_only=True)
    # keep a read-only formatted workspace for responses
    workspace = serializers.SerializerMethodField(read_only=True)
    tenant_name = serializers.ReadOnlyField(source="workspace.tenant.name")
    # accept workspace id in requests and map it to the model's workspace FK
    workspace_id = serializers.PrimaryKeyRelatedField(
        queryset=Workspace.objects.all(), write_only=True, source="workspace"
    )
    # accept location id in requests and map it to the model's location FK
    location_id = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.all(), write_only=True, source="location"
    )

    class Meta:
        model = Gateway
        fields = "__all__"

    def get_location(self, obj):
        location = obj.location
        if location:
            return {
                "id": location.id,
                "name": location.name,
                "latitude": location.latitude,
                "longitude": location.longitude,
                "altitude": location.altitude,
                "accuracy": location.accuracy,
                "source": location.source,
            }
        return None

    def get_workspace(self, obj):
        workspace = obj.workspace
        if workspace:
            return {
                "id": workspace.id,
                "name": workspace.name,
                "tenant_id": workspace.tenant.id if workspace.tenant else None,
                "tenant": workspace.tenant.name if workspace.tenant else None,
            }
        return None


class ActivationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Activation
        fields = "__all__"


class MeasurementsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Measurements
        fields = [
            "id",
            "min",
            "max",
            "threshold",
            "ref",
            "label",
            "unit",
            "icon",
            "require_consent",
        ]


class DeviceConsentSerializer(serializers.ModelSerializer):
    consented_measurement_ids = serializers.SerializerMethodField()
    device_eui = serializers.ReadOnlyField(source="device.dev_eui")
    device_name = serializers.ReadOnlyField(source="device.name")
    granted_by_username = serializers.ReadOnlyField(source="granted_by.username")
    revoked_by_username = serializers.ReadOnlyField(source="revoked_by.username")

    class Meta:
        model = DeviceConsent
        fields = [
            "id",
            "device",
            "device_eui",
            "device_name",
            "tenant",
            "workspace",
            "version",
            "status",
            "terms_version",
            "device_signature",
            "consented_measurements",
            "consented_measurement_ids",
            "granted_by",
            "granted_by_username",
            "granted_at",
            "revoked_by",
            "revoked_by_username",
            "revoked_at",
            "revocation_reason",
            "ip_address",
            "user_agent",
        ]
        read_only_fields = fields

    def get_consented_measurement_ids(self, obj):
        return list(obj.consented_measurements.values_list("id", flat=True))


class ConsentAcceptSerializer(serializers.Serializer):
    consented_measurement_ids = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list,
    )
    terms_version = serializers.CharField(
        max_length=50,
        required=False,
        default="v1.0",
    )

    def validate_consented_measurement_ids(self, value):
        device = self.context.get("device")
        if device and value:
            valid_ids = set(
                Measurements.objects.filter(device=device, id__in=value).values_list(
                    "id", flat=True
                )
            )
            invalid_ids = set(value) - valid_ids
            if invalid_ids:
                raise serializers.ValidationError(
                    f"Measurement IDs {list(invalid_ids)} do not belong to device {device.dev_eui}."
                )
        return value


class ConsentRevokeSerializer(serializers.Serializer):
    reason = serializers.CharField(
        required=True,
        allow_blank=False,
        min_length=1,
        error_messages={
            "blank": "Revocation reason cannot be blank.",
            "required": "Revocation reason is required.",
        },
    )

