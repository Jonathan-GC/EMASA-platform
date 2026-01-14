from django.db import models
from .hasher import generate_id


class Subscription(models.Model):
    id = models.CharField(
        max_length=16, primary_key=True, default=generate_id, editable=False
    )
    name = models.CharField(max_length=255)
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

    id = models.CharField(
        max_length=16, primary_key=True, default=generate_id, editable=False
    )
    cs_tenant_id = models.CharField(max_length=36, null=True, blank=True)
    name = models.CharField(max_length=90)
    img = models.FileField(upload_to="tenant_images/", blank=True, null=True)
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE)
    description = models.CharField(max_length=255, blank=True, null=True)
    sync_status = models.CharField(
        default=False,
        choices=[("PENDING", "Pending"), ("SYNCED", "Synced"), ("ERROR", "Error")],
        max_length=30,
    )
    sync_error = models.CharField(max_length=255, blank=True, null=True)
    last_synced_at = models.DateTimeField(auto_now=True)

    # Monitor
    is_global = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Workspace(models.Model):
    id = models.CharField(
        max_length=16, primary_key=True, default=generate_id, editable=False
    )
    name = models.CharField(max_length=80)
    img = models.FileField(upload_to="workspace_images/", blank=True, null=True)
    description = models.CharField(max_length=255)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

from auditlog.registry import auditlog
auditlog.register(Subscription)
auditlog.register(Tenant)
# Workspace is not defined in this file (based on read_file output), I should check if it exists in the file or imported.
# Based on file structure organizations/models.py should have Workspace too.
# Let me check the end of organizations/models.py first to be safe.
auditlog.register(Workspace)
