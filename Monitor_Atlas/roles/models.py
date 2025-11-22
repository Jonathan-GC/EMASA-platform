from django.db import models
from users.models import User
from organizations.models import Workspace

from django.contrib.auth.models import Group
from organizations.hasher import generate_id


class Role(models.Model):
    id = models.CharField(
        max_length=16, primary_key=True, default=generate_id, editable=False
    )
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
                name=f"{self.id}_{self.name}_{self.workspace.tenant.name}"
            )
            self.group = group
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.group:
            self.group.delete()
        super().delete(*args, **kwargs)

    def __str__(self):
        return self.name


class WorkspaceMembership(models.Model):
    # User's workspace membership
    id = models.CharField(
        max_length=16, primary_key=True, default=generate_id, editable=False
    )
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        if self.pk:
            try:
                old_membership = WorkspaceMembership.objects.get(pk=self.pk)
                old_group = old_membership.role.group if old_membership.role else None

                if old_group and old_group != (self.role.group if self.role else None):
                    self.user.groups.remove(old_group)
            except WorkspaceMembership.DoesNotExist:
                pass

        if self.role and self.role.group:
            self.user.groups.add(self.role.group)

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.role and self.role.group:
            self.user.groups.remove(self.role.group)
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.user} - {self.role}"
