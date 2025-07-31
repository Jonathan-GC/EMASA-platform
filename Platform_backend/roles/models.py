from django.db import models

from django.db import models
from users.models import User
from organizations.models import Workspace
from infrastructure.models import Node, Machine, Service


class Role(models.Model):
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    color = models.CharField(max_length=255)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class WorkspaceMembership(models.Model):
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user} - {self.workspace}"


class PermissionKey(models.Model):
    ACTION_MAP = {
        "list": "get",
        "retrieve": "get_by_id",
        "create": "post",
        "update": "put",
        "partial_update": "put",
        "destroy": "delete",
    }
    code = models.CharField(max_length=255, blank=True, null=True)
    scope = models.CharField(
        max_length=30,
        choices=[
            ("node", "Node"),
            ("machine", "Machine"),
            ("service", "Service"),
            ("user", "User"),
            ("role", "Role"),
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
        ]
    )

    node = models.ForeignKey(Node, on_delete=models.CASCADE, null=True, blank=True)
    machine = models.ForeignKey(
        Machine, on_delete=models.CASCADE, null=True, blank=True
    )
    service = models.ForeignKey(
        Service, on_delete=models.CASCADE, null=True, blank=True
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    role = models.ForeignKey(Role, on_delete=models.CASCADE, null=True, blank=True)

    @classmethod
    def from_view_action(cls, action):
        return cls.ACTION_MAP.get(action)

    def save(self, *args, **kwargs):
        entity_id = (
            self.node_id or self.machine_id or self.service_id
            or self.user_id or self.role_id or "*"
        )
        self.code = f"{self.scope}:{entity_id}:{self.key_type}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.code

class RolePermission(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    permission_key = models.ForeignKey(PermissionKey, on_delete=models.CASCADE)