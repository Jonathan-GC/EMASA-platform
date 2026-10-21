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
    is_global = models.BooleanField(default=False, db_index=True)

    SECURITY_LEVEL_CHOICES = [
        ("NONE", "None"),
        ("LOW", "Low"),
        ("MEDIUM", "Medium"),
        ("HIGH", "High"),
    ]
    security_level = models.CharField(
        max_length=10,
        choices=SECURITY_LEVEL_CHOICES,
        default="MEDIUM",
        db_index=True,
    )

    @property
    def trust_score_threshold(self) -> int:
        mapping = {"NONE": 0, "LOW": 60, "MEDIUM": 75, "HIGH": 101}
        return mapping.get(self.security_level, 75)

    @property
    def device_trust_ttl_days(self) -> int:
        mapping = {"LOW": 60, "MEDIUM": 30, "HIGH": 0, "NONE": 0}
        return mapping.get(self.security_level, 30)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["is_global"],
                condition=models.Q(is_global=True),
                name="unique_global_tenant",
            )
        ]

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
auditlog.register(
    Tenant, exclude_fields=["last_synced_at", "sync_error", "sync_status"]
)
auditlog.register(Workspace)
