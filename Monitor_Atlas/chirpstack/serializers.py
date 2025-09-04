from .models import DeviceProfile, DeviceProfileTemplate, ApiUser
from rest_framework import serializers


class DeviceProfileSerializer(serializers.ModelSerializer):
    workspace = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = DeviceProfile
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


class DeviceProfileTemplateSerializer(serializers.ModelSerializer):
    workspace = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = DeviceProfileTemplate
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


class ApiUserSerializer(serializers.ModelSerializer):
    workspace = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ApiUser
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
