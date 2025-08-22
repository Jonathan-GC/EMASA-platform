from django.db import models

class Subscription(models.Model):
    name = models.CharField(max_length=30)
    description = models.CharField(max_length=255)
    can_have_gateways = models.BooleanField(default=False)
    max_device_count = models.IntegerField(default=0)
    max_gateway_count = models.IntegerField(default=0)

    def __str__(self):
        return self.name

class Tenant(models.Model):
    api_id=models.CharField(max_length=30)
    name = models.CharField(max_length=90)
    img = models.CharField(max_length=255, blank=True, null=True)
    suscription = models.ForeignKey(Subscription, on_delete=models.CASCADE)
    group = models.CharField(max_length=30)
    description = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.name
    
class Workspace(models.Model):
    name = models.CharField(max_length=80)
    img = models.CharField(max_length=255, blank=True, null=True)
    description = models.CharField(max_length=255)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} - {self.tenant}"