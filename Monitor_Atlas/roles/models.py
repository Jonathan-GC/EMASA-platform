from django.db import models
from users.models import User
from organizations.models import Workspace

from django.contrib.auth.models import Group


class Role(models.Model):
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True)
    color = models.CharField(max_length=20, default="#bfbfbf")
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)
    is_admin = models.BooleanField(
        default=False
    )  # Admin in workspace and tenant context
    group = models.OneToOneField(Group, on_delete=models.CASCADE, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.pk and not self.group:
            group = Group.objects.create(
                name=f"{self.name}_{self.workspace.tenant.name}"
            )
            self.group = group
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.group:
            self.group.delete()
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - {self.workspace}"


class WorkspaceMembership(models.Model):
    # User's workspace membership
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        # Ensure the user's groups are updated based on their role
        if self.role and self.role.group:
            self.user.groups.clear()
            self.user.groups.add(self.role.group)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.role and self.role.group:
            self.user.groups.remove(self.role.group)
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"Membership: {self.user} - {self.role} - {self.workspace}"
