from django.db import models

from django.db import models
from users.models import User
from organizations.models import Workspace, Tenant, Subscription
from infrastructure.models import Device, Machine, Application, Gateway, Location, Type
from chirpstack.models import DeviceProfile, DeviceProfileTemplate, ApiUser


class Role(models.Model):
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True)
    color = models.CharField(max_length=20, default="#bfbfbf")  # Hex tag color
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)
    is_admin = models.BooleanField(
        default=False
    )  # Admin in workspace and tenant context

    def __str__(self):
        return f"{self.name} - {self.workspace}"


class WorkspaceMembership(models.Model):
    # User's workspace membership
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)

    def __str__(self):
        return f"Membership: {self.user} - {self.role} - {self.workspace}"


class PermissionKey(models.Model):
    # ACTION_MAP Translates DRF actions to permission keys
    ACTION_MAP = {
        "list": ["get"],
        "retrieve": ["get", "get_by_id"],
        "create": ["post"],
        "update": ["put"],
        "partial_update": ["put"],
        "destroy": ["delete"],
        "set_activation": ["post"],
        "activate": ["post"],
        "deactivate": ["post"],
        "get_ws_link": ["post"],
        "get_all_permission_keys_by_role": ["get"],
    }
    code = models.CharField(
        max_length=50, blank=True, null=True
    )  # Code is auto-generated
    # Scope may vary depending on the resource and new additions
    scope = models.CharField(
        max_length=30,
        choices=[
            ("device", "Device"),
            ("machine", "Machine"),
            ("application", "Application"),
            ("user", "User"),
            ("role", "Role"),
            ("workspace", "Workspace"),
            ("tenant", "Tenant"),
            ("location", "Location"),
            ("gateway", "Gateway"),
            ("device_profile", "DeviceProfile"),
            ("device_profile_template", "DeviceProfileTemplate"),
            ("api_user", "ApiUser"),
            ("type", "Type"),
            ("subscription", "Subscription"),
        ],
    )
    key_type = models.CharField(
        max_length=30,
        choices=[
            ("get", "Get"),
            ("get_by_id", "Get By ID"),
            ("put", "Put"),
            ("post", "Post"),
            ("delete", "Delete"),
        ],
    )

    # Object based permissions
    device = models.ForeignKey(Device, on_delete=models.CASCADE, null=True, blank=True)
    machine = models.ForeignKey(
        Machine, on_delete=models.CASCADE, null=True, blank=True
    )
    application = models.ForeignKey(
        Application, on_delete=models.CASCADE, null=True, blank=True
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    role = models.ForeignKey(Role, on_delete=models.CASCADE, null=True, blank=True)
    workspace = models.ForeignKey(
        Workspace, on_delete=models.CASCADE, null=True, blank=True
    )
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True)
    location = models.ForeignKey(
        Location, on_delete=models.CASCADE, null=True, blank=True
    )
    gateway = models.ForeignKey(
        Gateway, on_delete=models.CASCADE, null=True, blank=True
    )
    device_profile = models.ForeignKey(
        DeviceProfile, on_delete=models.CASCADE, null=True, blank=True
    )
    device_profile_template = models.ForeignKey(
        DeviceProfileTemplate, on_delete=models.CASCADE, null=True, blank=True
    )
    api_user = models.ForeignKey(
        ApiUser, on_delete=models.CASCADE, null=True, blank=True
    )
    type = models.ForeignKey(Type, on_delete=models.CASCADE, null=True, blank=True)
    subscription = models.ForeignKey(
        Subscription, on_delete=models.CASCADE, null=True, blank=True
    )

    @classmethod
    def from_view_action(cls, action):
        return cls.ACTION_MAP.get(action, [])

    def save(self, *args, **kwargs):
        """
        Generate a code for this permission key based on the scope, entity id,
        and key type. The code is in the format of "scope:entity_id:key_type".
        If the entity id is None, it is replaced with "*".
        """
        entity_id = (
            self.device_id
            or self.machine_id
            or self.application_id
            or self.user_id
            or self.role_id
            or self.workspace_id
            or self.tenant_id
            or self.location_id
            or self.gateway_id
            or self.device_profile_id
            or self.device_profile_template_id
            or self.api_user_id
            or self.subscription_id
            or self.type_id
            or "*"
        )
        self.code = f"{self.scope}:{entity_id}:{self.key_type}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.code


class RolePermission(models.Model):
    # Assign permissions to roles
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    permission_key = models.ForeignKey(
        PermissionKey, on_delete=models.CASCADE, related_name="rolepermissions"
    )

    def __str__(self):
        return f"{self.role} - {self.permission_key}"
