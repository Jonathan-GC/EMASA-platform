from rest_framework import serializers
from .models import Role, WorkspaceMembership, PermissionKey, RolePermission
from organizations.models import Workspace
from users.models import User


class RoleSerializer(serializers.ModelSerializer):
    """
    Serializer for the Role model.
    Allows serialization and validation of the fields of a role within a workspace.
    """

    workspace = serializers.SerializerMethodField(read_only=True)
    workspace_id = serializers.PrimaryKeyRelatedField(
        queryset=Workspace.objects.all(), write_only=True, source="workspace"
    )

    class Meta:
        model = Role
        fields = "__all__"

    def validate_name(self, value):
        """
        Validates that the name of the role has at least 3 characters.
        """
        if len(value.strip()) < 3:
            raise serializers.ValidationError(
                "The name of the role must have at least 3 characters."
            )
        return value

    def validate_color(self, value):
        """
        Validates that the color is in hexadecimal format (e.g. #FF5733).
        """
        if not value.startswith("#") or len(value) != 7:
            raise serializers.ValidationError(
                "The color must be in hexadecimal format (e.g. #FF5733)."
            )
        return value

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


class WorkspaceMembershipSerializer(serializers.ModelSerializer):
    """
    Serializer for the WorkspaceMembership model.
    Allows serialization and validation of the membership of a user in a workspace.
    """

    user = serializers.SerializerMethodField(read_only=True)
    role = serializers.SerializerMethodField(read_only=True)
    workspace = serializers.SerializerMethodField(read_only=True)
    workspace_id = serializers.PrimaryKeyRelatedField(
        queryset=Workspace.objects.all(), write_only=True, source="workspace"
    )
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), write_only=True, source="user"
    )
    role_id = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.all(), write_only=True, source="role"
    )

    class Meta:
        model = WorkspaceMembership
        fields = "__all__"

    def validate(self, data):
        """
        Validates that the user is not already registered as a member in the same workspace.
        """
        user = data.get("user")
        workspace = data.get("workspace")

        if WorkspaceMembership.objects.filter(user=user, workspace=workspace).exists():
            raise serializers.ValidationError(
                "This user is already a member of this workspace."
            )

        return data

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

    def get_user(self, obj):
        user = obj.user
        if user:
            return {
                "id": user.id,
                "username": user.username,
                "email": user.email,
            }
        return None

    def get_role(self, obj):
        role = obj.role
        if role:
            return {
                "id": role.id,
                "name": role.name,
                "color": role.color,
            }
        return None


class PermissionKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = PermissionKey
        fields = "__all__"

    def validate(self, attrs):
        """
        Validates that the required field for the given scope is present in the attributes.
        Raises a ValidationError if the required field for the specified scope is missing.
        """
        scope = attrs.get("scope")
        required_fields = {
            "device": "device_id",
            "machine": "machine_id",
            "application": "application_id",
            "user": "user_id",
            "role": "role_id",
            "workspace": "workspace_id",
            "tenant": "tenant_id",
            "location": "location_id",
            "gateway": "gateway_id",
            "device_profile": "device_profile_id",
            "device_profile_template": "device_profile_template_id",
            "api_user": "api_user_id",
            "type": "type_id",
            "subscription": "subscription_id",
        }
        required_field = required_fields.get(scope)
        if required_field and not attrs.get(required_field):
            raise serializers.ValidationError(
                f"{required_field.capitalize()} is required for {scope} scope"
            )
        return attrs


class RolePermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RolePermission
        fields = "__all__"
