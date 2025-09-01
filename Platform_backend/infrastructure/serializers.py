from .models import Machine, Type, Device, Application, Gateway, Location
from rest_framework import serializers
from organizations.serializers import WorkspaceSerializer


class MachineSerializer(serializers.ModelSerializer):
    workspace = serializers.SerializerMethodField(read_only=True)

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
    location = LocationSerializer()
    workspace = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Gateway
        fields = "__all__"

    def create(self, validated_data):
        location_data = validated_data.pop("location")
        location = Location.objects.create(**location_data)
        gateway = Gateway.objects.create(location=location, **validated_data)
        return gateway

    def update(self, instance, validated_data):
        location = validated_data.pop("location", None)

        if location:
            location_instance = instance.location

            for attr, value in location.items():
                setattr(location_instance, attr, value)
            location_instance.save()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance

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
