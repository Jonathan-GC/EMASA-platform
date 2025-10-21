from django.db import models
from users.models import User
from organizations.models import Workspace


class Role(models.Model):
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True)
    color = models.CharField(max_length=20, default="#bfbfbf")  # Hex tag color
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)
    is_admin = models.BooleanField(
        default=False
    )  # Admin in workspace and tenant context

    class Meta:
        permissions = (
            ("manage_roles", "Can manage roles"),
            ("assign_roles", "Can assign roles to users"),
        )

    def __str__(self):
        return f"{self.name} - {self.workspace}"


class WorkspaceMembership(models.Model):
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("workspace", "user")
        permissions = (("manage_memberships", "Can manage workspace memberships"),)

    def __str__(self):
        return f"Membership: {self.user} - {self.role} - {self.workspace}"
