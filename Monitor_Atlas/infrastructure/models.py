from django.db import models
from organizations.models import Workspace
from chirpstack.models import DeviceProfile
from organizations.hasher import generate_id


class Machine(models.Model):
    id = models.CharField(
        max_length=16, primary_key=True, default=generate_id, editable=False
    )
    name = models.CharField(max_length=255)
    img = models.FileField(upload_to="machine_icons/", blank=True, null=True)
    description = models.CharField(max_length=255, blank=True)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} - {self.workspace}"


class Type(models.Model):
    id = models.CharField(
        max_length=16, primary_key=True, default=generate_id, editable=False
    )
    name = models.CharField(max_length=255, unique=True)
    img = models.CharField(max_length=50, blank=True, null=True)  # icon
    description = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.name}"


class Application(models.Model):
    """
    Chirpstack object payload:
        "application": {
            "name": "string",
            "description": "string",
            "tenantId": "string"
        }
    """

    id = models.CharField(
        max_length=16, primary_key=True, default=generate_id, editable=False
    )
    cs_application_id = models.CharField(
        max_length=36,
        unique=True,
        null=True,
        blank=True,
        help_text="Application ID (Chirpstack)",
    )  # cs
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255, default="")
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)
    sync_status = models.CharField(
        default=False,
        choices=[("PENDING", "Pending"), ("SYNCED", "Synced"), ("ERROR", "Error")],
        max_length=30,
    )
    sync_error = models.CharField(max_length=255, blank=True, null=True)
    last_synced_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Activation(models.Model):
    """
    Chirpstack device activation payload (dev_eui in params):

    "deviceActivation": {
                "aFCntDown": 0,
                "appSKey": "53C020841486263981FA77355D278762",
                "devAddr": "260CB229",
                "fCntUp": 0,
                "fNwkSIntKey": "4978CB8E7FFBD46BC570FE11F17FA56E",
                "nFCntDown": 0,
                "nwkSEncKey": "4978CB8E7FFBD46BC570FE11F17FA56E",
                "sNwkSIntKey": "4978CB8E7FFBD46BC570FE11F17FA56E"
        }
    """

    id = models.CharField(
        max_length=16, primary_key=True, default=generate_id, editable=False
    )
    afcntdown = models.IntegerField()
    app_s_key = models.CharField(
        max_length=32, help_text="Application session key (Chirpstack)"
    )  # cs
    dev_addr = models.CharField(
        max_length=8, help_text="Device address (Chirpstack)"
    )  # cs
    f_cnt_up = models.IntegerField()
    f_nwk_s_int_key = models.CharField(
        max_length=32, help_text="Network session key (Chirpstack)"
    )  # cs
    n_f_cnt_down = models.IntegerField()
    nwk_s_enc_key = models.CharField(
        max_length=32, help_text="Network session key (Chirpstack)"
    )  # cs
    s_nwk_s_int_key = models.CharField(
        max_length=32, help_text="Network session key (Chirpstack)", default=""
    )  # cs


class Device(models.Model):
    """
    Chirpstack object payload:
        "device": {
            "name": "test-device",
            "description": "this is a test devname",
            "devEui": "70B3D57ED006E229",
            "deviceProfileId": "753a922b-ab01-42a2-87dc-a05c34fd32d3",
            "isDisabled": false,
            "applicationId": "string"
        }
    """

    id = models.CharField(
        max_length=16, primary_key=True, default=generate_id, editable=False
    )
    dev_eui = models.CharField(
        max_length=16, help_text="Device EUI (Chirpstack)", unique=True
    )  # cs
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    machine = models.ForeignKey(
        Machine, on_delete=models.PROTECT, null=True, blank=True
    )
    workspace = models.ForeignKey(
        Workspace, on_delete=models.CASCADE
    )  # cs Workspace.Tenant
    device_type = models.ForeignKey(
        Type, on_delete=models.CASCADE
    )  # icon, classification and such
    device_profile = models.ForeignKey(
        DeviceProfile, on_delete=models.CASCADE, help_text="Device profile (Chirpstack)"
    )  # cs
    application = models.ForeignKey(
        Application, on_delete=models.CASCADE, help_text="Application (Chirpstack)"
    )  # cs
    is_disabled = models.BooleanField(default=False)
    last_seen_at = models.DateTimeField(null=True, blank=True)
    sync_status = models.CharField(
        default=False,
        choices=[("PENDING", "Pending"), ("SYNCED", "Synced"), ("ERROR", "Error")],
        max_length=30,
    )
    sync_error = models.CharField(max_length=255, blank=True, null=True)
    last_synced_at = models.DateTimeField(auto_now=True)
    enabled_activation = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    activation = models.ForeignKey(
        Activation, on_delete=models.PROTECT, null=True, blank=True
    )

    def save(self, *args, **kwargs):
        if not self.pk:
            self.dev_eui = self.dev_eui.lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Location(models.Model):
    # Chirpstack
    id = models.CharField(
        max_length=16, primary_key=True, default=generate_id, editable=False
    )
    name = models.CharField(max_length=255, default="Unknown", null=True, blank=True)
    accuracy = models.FloatField(default=0.0, null=True, blank=True)
    altitude = models.FloatField(default=0.0, null=True, blank=True)
    latitude = models.FloatField(default=0.0, null=True, blank=True)
    longitude = models.FloatField(default=0.0, null=True, blank=True)
    source = models.CharField(
        choices=[
            ("UNKNOWN", "Unknown"),
            ("GPS", "GPS"),
            ("CONFIG", "Manually configured"),
            ("GEO_RESOLVER_TDOA", "Geo resolver (TDOA)"),
            ("GEO_RESOLVER_RSSI", "Geo resolver (RSSI)"),
            ("GEO_RESOLVER_GNSS", "Geo resolver (GNSS)"),
            ("GEO_RESOLVER_WIFI", "Geo resolver (WiFi)"),
        ],
        default="UNKNOWN",
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"{self.name}"


class Gateway(models.Model):
    """
    Chirpstack object payload:
        "gateway": {
            "gatewayId": "a84041fdfe2764b6",
            "name": "test-api",
            "description": "this is a test gateway",
            "statsInterval": 30,
            "tenantId": "string"
            "location": {
                "accuracy": 0,
                "altitude": 0,
                "latitude": 0,
                "longitude": 0,
                "source": "UNKNOWN"
            }
        }
    """

    id = models.CharField(
        max_length=16, primary_key=True, default=generate_id, editable=False
    )
    cs_gateway_id = models.CharField(max_length=36, unique=True)  # cs
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    stats_interval = models.IntegerField(default=30)  # Cs in seconds
    location = models.ForeignKey(Location, on_delete=models.CASCADE)  # Cs
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)  # cs
    state = models.CharField(max_length=30, null=True, blank=True)  # cs
    last_seen_at = models.DateTimeField(null=True, blank=True)
    sync_status = models.CharField(
        default=False,
        choices=[("PENDING", "Pending"), ("SYNCED", "Synced"), ("ERROR", "Error")],
        max_length=30,
    )
    sync_error = models.CharField(max_length=255, blank=True, null=True)
    last_synced_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name}"


class Measurements(models.Model):
    id = models.CharField(
        max_length=16, primary_key=True, default=generate_id, editable=False
    )
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    min = models.FloatField()
    max = models.FloatField()
    threshold = models.FloatField()
    unit = models.CharField(max_length=50)
    ref = models.CharField(max_length=100, blank=True, null=True)
    icon = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"{self.device.name} - {self.unit}"
