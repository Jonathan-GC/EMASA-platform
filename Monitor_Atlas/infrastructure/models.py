from django.db import models
from organizations.models import Workspace
from chirpstack.models import DeviceProfile


class Machine(models.Model):
    name = models.CharField(max_length=255)
    img = models.CharField(max_length=255, blank=True, null=True)
    description = models.CharField(max_length=255, blank=True)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)

    class Meta:
        permissions = (
            ("manage_machines", "Can manage machines"),
            ("view_machine_details", "Can view machine details"),
        )

    def __str__(self):
        return f"{self.name} - {self.workspace}"


class Type(models.Model):
    name = models.CharField(max_length=255, unique=True)
    img = models.CharField(max_length=255, blank=True, null=True)  # icon
    description = models.CharField(max_length=255)

    class Meta:
        permissions = (
            ("manage_type", "Can manage device type"),
            ("view_type_details", "Can view device type details"),
        )

    def __str__(self):
        return f"{self.name}"


class Application(models.Model):
    cs_application_id = models.CharField(
        max_length=36,
        unique=True,
        null=True,
        blank=True,
        help_text="Application ID (Chirpstack)",
    )  # cs
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255, default="")
    device_type = models.ForeignKey(
        Type,
        on_delete=models.CASCADE,
        help_text="You can classify devices by type and set a custom icon",
    )  # icon, classification and such
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)

    # Sync status
    sync_status = models.CharField(
        default=False,
        choices=[("PENDING", "Pending"), ("SYNCED", "Synced"), ("ERROR", "Error")],
        max_length=30,
    )
    sync_error = models.CharField(max_length=255, blank=True, null=True)
    last_synced_at = models.DateTimeField(auto_now=True)

    class Meta:
        permissions = (
            ("manage_application", "Can manage application"),
            ("sync_application", "Can sync application with Chirpstack"),
        )

    def __str__(self):
        return f"{self.cs_application_id} - {self.name}"


class Activation(models.Model):
    a_f_cnt_down = models.IntegerField()
    app_s_key = models.CharField(
        max_length=32, help_text="Application session key (Chirpstack)"
    )
    dev_addr = models.CharField(max_length=8, help_text="Device address (Chirpstack)")
    f_cnt_up = models.IntegerField()
    f_nwk_s_int_key = models.CharField(
        max_length=32, help_text="Network session key (Chirpstack)"
    )
    n_f_cnt_down = models.IntegerField()
    nwk_s_enc_key = models.CharField(
        max_length=32, help_text="Network session key (Chirpstack)"
    )
    s_nwk_s_int_key = models.CharField(
        max_length=32, help_text="Network session key (Chirpstack)", default=""
    )

    class Meta:
        permissions = (("manage_activation", "Can manage device activation"),)

    def __str__(self):
        return f"{self.dev_addr}"


class Device(models.Model):
    dev_eui = models.CharField(
        max_length=16, help_text="Device EUI (Chirpstack)", unique=True
    )
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)
    device_type = models.ForeignKey(Type, on_delete=models.CASCADE)
    device_profile = models.ForeignKey(
        DeviceProfile, on_delete=models.CASCADE, help_text="Device profile (Chirpstack)"
    )
    application = models.ForeignKey(
        Application, on_delete=models.CASCADE, help_text="Application (Chirpstack)"
    )
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
        Activation, on_delete=models.CASCADE, null=True, blank=True
    )

    class Meta:
        permissions = (
            ("manage_device", "Can manage device"),
            ("activate_device", "Can activate device"),
            ("view_device_details", "Can view device details"),
        )

    def __str__(self):
        return f"{self.dev_eui} - {self.name}"


class Location(models.Model):
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
        max_length=30,
        null=True,
        blank=True,
    )

    class Meta:
        permissions = (
            ("manage_location", "Can manage location"),
            ("view_location_details", "Can view location details"),
        )

    def __str__(self):
        return f"{self.name}"


class Gateway(models.Model):
    cs_gateway_id = models.CharField(max_length=36, unique=True)  # cs
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    stats_interval = models.IntegerField(default=30)  # Cs in seconds
    location = models.ForeignKey(Location, on_delete=models.CASCADE)  # Cs
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)  # cs
    state = models.CharField(max_length=30, null=True, blank=True)  # cs
    last_seen_at = models.DateTimeField(null=True, blank=True)

    # Sync status
    sync_status = models.CharField(
        default=False,
        choices=[("PENDING", "Pending"), ("SYNCED", "Synced"), ("ERROR", "Error")],
        max_length=30,
    )
    sync_error = models.CharField(max_length=255, blank=True, null=True)
    last_synced_at = models.DateTimeField(auto_now=True)

    class Meta:
        permissions = (
            ("manage_gateway", "Can manage gateway"),
            ("sync_gateway", "Can sync gateway with Chirpstack"),
            ("view_gateway_details", "Can view gateway details"),
        )

    def __str__(self):
        return f"{self.name} - {self.workspace}"
