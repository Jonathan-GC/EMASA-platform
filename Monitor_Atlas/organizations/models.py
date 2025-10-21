from django.db import models
from django_tenants.models import TenantMixin, DomainMixin


class Subscription(models.Model):
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    can_have_gateways = models.BooleanField(default=False)
    max_device_count = models.IntegerField(default=0)
    max_gateway_count = models.IntegerField(default=0)

    def __str__(self):
        return self.name


class Tenant(TenantMixin):
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

    cs_tenant_id = models.CharField(max_length=36, null=True, blank=True)
    name = models.CharField(max_length=90)
    img = models.CharField(max_length=255, blank=True, null=True)
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE)
    description = models.CharField(max_length=255, blank=True, null=True)

    # Sync status
    sync_status = models.CharField(
        default=False,
        choices=[("PENDING", "Pending"), ("SYNCED", "Synced"), ("ERROR", "Error")],
        max_length=30,
    )
    sync_error = models.CharField(max_length=255, blank=True, null=True)
    last_synced_at = models.DateTimeField(auto_now=True)

    is_super_tenant = models.BooleanField(
        default=False,
    )

    def save(self, *args, **kwargs):
        if not self.schema_name:
            if self.name == "EMASA":
                self.schema_name = "public"
                self.is_super_tenant = True
            else:
                clean_name = self.name.lower().replace(" ", "_")
                self.schema_name = f"tenant_{clean_name}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.schema_name})"


class Domain(DomainMixin):
    pass

    class Meta:
        db_table = "organizations_domain"


class Workspace(models.Model):
    name = models.CharField(max_length=80)
    img = models.CharField(max_length=255, blank=True, null=True)
    description = models.CharField(max_length=255)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)

    class Meta:
        permissions = (
            ("manage_workspace", "Can manage workspace"),
            ("view_workspace_details", "Can view workspace details"),
        )

    def __str__(self):
        return f"{self.name} - {self.tenant}"
