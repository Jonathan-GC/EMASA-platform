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
    """
    Chirpstack Tenant creation payload:
        {
        "canHaveGateways": true,
		"description": "string",
		"maxDeviceCount": 0,
		"maxGatewayCount": 0,
		"name": "tecnobot999",
		"privateGatewaysDown": true,
		"privateGatewaysUp": true,
        }
    """
    cs_tenant_id=models.CharField(max_length=36, null=True, blank=True)
    name = models.CharField(max_length=90)
    img = models.CharField(max_length=255, blank=True, null=True)
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE)
    group = models.CharField(max_length=30)
    description = models.CharField(max_length=255, blank=True, null=True)
    sync_status = models.CharField(
        default=False,
        choices=[
            ("PENDING", "Pending"),
            ("SYNCED", "Synced"),
            ("ERROR", "Error")
            ],
        max_length=30,
    )
    sync_error = models.CharField(max_length=255, blank=True, null=True)
    last_synced_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.name
    
class Workspace(models.Model):
    name = models.CharField(max_length=80)
    img = models.CharField(max_length=255, blank=True, null=True)
    description = models.CharField(max_length=255)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} - {self.tenant}"