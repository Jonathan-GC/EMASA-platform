from django.db import models
from organizations.models import Tenant

# Create your models here.

class ApiUser(models.Model):
    api_id=models.CharField(max_length=30)
    email = models.EmailField()
    password = models.CharField(max_length=30)
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    note = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.api_id} - {self.email}"

class TenantUser(models.Model):
    api_id=models.CharField(max_length=30)
    user=models.ForeignKey(ApiUser, on_delete=models.CASCADE)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    is_admin = models.BooleanField(default=False)
    is_device_admin = models.BooleanField(default=False)
    is_gateway_admin = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.api_id} - {self.user}"

class DeviceProfileTemplate(models.Model):
    api_id=models.CharField(max_length=30)
    name = models.CharField(max_length=30)
    description = models.CharField(max_length=255)
    region = models.CharField(max_length=30)
    vendor = models.CharField(max_length=30)
    mac_version = models.CharField(max_length=30)
    reg_param_revision = models.CharField(max_length=30, default="A")
    abp_rx1_delay = models.IntegerField()
    abp_rx1_dr_offset = models.IntegerField()
    abp_rx2_dr = models.IntegerField()
    abp_rx2_freq = models.IntegerField()
    adr_algorithm = models.CharField(max_length=30)
    firmware = models.CharField(max_length=255)
    flush_queue_on_activate = models.BooleanField(default=False)
    supports_otaa = models.BooleanField(default=False)
    supports_class_b = models.BooleanField(default=False)
    supports_class_c = models.BooleanField(default=False)
    payload_codec_runtime = models.CharField(max_length=30, default="JS")
    payload_codec_script = models.CharField(max_length=255)
    uplink_interval = models.IntegerField(default=18)
    auto_detect_measurements = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.api_id} - {self.name}"
    
class DeviceProfile(models.Model):
    api_id=models.CharField(max_length=30)
    name = models.CharField(max_length=30)
    description = models.CharField(max_length=255)
    region = models.CharField(max_length=30)
    vendor = models.CharField(max_length=30, default="EMASA")
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
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
        return f"{self.api_id} - {self.name}"
    

