from django.db import models
from organizations.models import Workspace

# Create your models here.


class ApiUser(models.Model):
    """
    Chirpstack API User payload:
    {
        "password": "123",
        "tenants": [
                {
                    "isAdmin": true,
                    "isDeviceAdmin": true,
                    "isGatewayAdmin": true,
                    "tenantId": "b5adddf6-8ad0-46ca-923c-9a8b13b14304"
                }
        ],
        "user": {
                    "email": "user2@tenant.com",
                    "isActive": true,
                    "isAdmin": false,
                    "note": "this a user of the chiprstack default tenant"
                }
        }
    """

    cs_user_id = models.CharField(max_length=36, unique=True, null=True, blank=True)
    email = models.EmailField()
    password = models.CharField(max_length=30, blank=True, null=True)
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    note = models.CharField(max_length=255, blank=True, null=True)
    workspace = models.ForeignKey(
        Workspace, on_delete=models.CASCADE, null=True, blank=True
    )
    is_tenant_admin = models.BooleanField(default=False)
    is_tenant_device_admin = models.BooleanField(default=False)
    is_tenant_gateway_admin = models.BooleanField(default=False)
    sync_status = models.CharField(
        default="PENDING",
        choices=[("PENDING", "Pending"), ("SYNCED", "Synced"), ("ERROR", "Error")],
        max_length=30,
    )
    sync_error = models.CharField(max_length=255, blank=True, null=True, default="")
    last_synced_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.email


class DeviceProfileTemplate(models.Model):
    """
    This model is not necesary for chirpstack, but we left it to help make device profile creation easier
    """

    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    region = models.CharField(max_length=30)
    vendor = models.CharField(max_length=30, default="EMASA")
    workspace = models.ForeignKey(
        Workspace, on_delete=models.CASCADE, null=True, blank=True
    )
    mac_version = models.CharField(max_length=30, default="LORAWAN_1_0_3")
    reg_param_revision = models.CharField(max_length=30, default="A")
    abp_rx1_delay = models.IntegerField()
    abp_rx1_dr_offset = models.IntegerField()
    abp_rx2_dr = models.IntegerField()
    abp_rx2_freq = models.IntegerField()
    supports_class_b = models.BooleanField(default=False)
    supports_class_c = models.BooleanField(default=False)
    payload_codec_runtime = models.CharField(max_length=30, default="JS")
    is_rlay = models.BooleanField(default=False)
    is_rlay_ed = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class DeviceProfile(models.Model):
    cs_device_profile_id = models.CharField(
        max_length=36, unique=True, null=True, blank=True
    )
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    region = models.CharField(max_length=30)
    workspace = models.ForeignKey(
        Workspace, on_delete=models.CASCADE, null=True, blank=True
    )
    mac_version = models.CharField(max_length=30, default="LORAWAN_1_0_3")
    adr_algorithm_id = models.CharField(max_length=30, default="default")
    reg_param_revision = models.CharField(max_length=30, default="A")
    abp_rx1_delay = models.IntegerField()
    abp_rx1_dr_offset = models.IntegerField()
    abp_rx2_dr = models.IntegerField()
    abp_rx2_freq = models.IntegerField()
    supports_otaa = models.BooleanField(default=False)
    supports_class_b = models.BooleanField(default=False)
    supports_class_c = models.BooleanField(default=False)
    payload_codec_runtime = models.CharField(max_length=30, default="JS")
    payload_codec_script = models.TextField(blank=True, null=True)
    is_rlay = models.BooleanField(default=False)
    is_rlay_ed = models.BooleanField(default=False)
    flush_queue_on_activate = models.BooleanField(default=True)
    uplink_interval = models.IntegerField(default=3000)  # in seconds
    sync_status = models.CharField(
        default="PENDING",
        choices=[("PENDING", "Pending"), ("SYNCED", "Synced"), ("ERROR", "Error")],
        max_length=30,
    )
    sync_error = models.CharField(max_length=255, blank=True, null=True, default="")
    last_synced_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
