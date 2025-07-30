from django.db import models

from django.db import models
from users.models import User
from organizations.models import Workspace


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