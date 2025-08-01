from django.db import models

class Region(models.Model):
    name = models.CharField(max_length=30, unique=True)
    img = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.name

class Organization(models.Model):
    name = models.CharField(max_length=90)
    img = models.CharField(max_length=255, blank=True, null=True)
    region = models.ForeignKey(Region, on_delete=models.CASCADE)

    def __str__(self):
        return self.name
    
class Workspace(models.Model):
    name = models.CharField(max_length=80, unique=True)
    img = models.CharField(max_length=255, blank=True, null=True)
    description = models.CharField(max_length=255)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} - {self.organization}"