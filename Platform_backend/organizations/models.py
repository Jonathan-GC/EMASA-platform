from django.db import models

from .mixins import PrefixMixin

class Region(models.Model, PrefixMixin):
    name = models.CharField(max_length=255)
    img = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Organization(models.Model, PrefixMixin):
    name = models.CharField(max_length=255)
    img = models.CharField(max_length=255)
    region = models.ForeignKey(Region, on_delete=models.CASCADE)

    def __str__(self):
        return self.name
    
class Workspace(models.Model, PrefixMixin):
    name = models.CharField(max_length=255)
    img = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} - {self.organization}"