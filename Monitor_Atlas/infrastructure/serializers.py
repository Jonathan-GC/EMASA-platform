from .models import (
    Machine,
    Type,
    Device,
    Application,
    Gateway,
    Location,
    Activation,
    Measurements,
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
        fields = "__all__"
