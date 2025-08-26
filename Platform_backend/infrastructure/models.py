from django.db import models
from organizations.models import Workspace
from chirpstack.models import DeviceProfile

class Machine(models.Model):
    name = models.CharField(max_length=30)
    img = models.CharField(max_length=255, blank=True, null=True)
    description = models.CharField(max_length=255, blank=True)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} - {self.workspace}"

class Type(models.Model):
    name = models.CharField(max_length=30, unique=True)
    img = models.CharField(max_length=255, blank=True, null=True) # icon
    description = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.name}"

class Application(models.Model):
    cs_application_id=models.CharField(max_length=36, help_text="Application ID (Chirpstack)") # cs
    name = models.CharField(max_length=30)
    device_type = models.ForeignKey(Type, on_delete=models.CASCADE, help_text="You can classify devices by type and set a custom icon") # icon, classification and such
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)
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
        return f"{self.cs_application_id} - {self.name}"
    
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
    
    dev_eui = models.CharField(max_length=16, help_text="Device EUI (Chirpstack)") # cs
    name = models.CharField(max_length=30)
    description = models.CharField(max_length=255)
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)
    device_type = models.ForeignKey(Type, on_delete=models.CASCADE) # icon, classification and such
    device_profile = models.ForeignKey(DeviceProfile, on_delete=models.CASCADE, help_text="Device profile (Chirpstack)") # cs
    application = models.ForeignKey(Application, on_delete=models.CASCADE, help_text="Application (Chirpstack)") # cs
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
        return f"{self.dev_eui} - {self.name}"

class Location(models.Model):
    # Chirpstack
    name = models.CharField(max_length=30)
    accuracy = models.FloatField()
    altitude = models.FloatField()
    latitude = models.FloatField()
    longitude = models.FloatField()
    source = models.CharField(
        choices=[
            ("UNKNOWN", "Unknown"),
            ("GPS", "GPS"),
            ("CONFIG", "Manually configured"),
            ("GEO_RESOLVER_TDOA", "Geo resolver (TDOA)"),
            ("GEO_RESOLVER_RSSI", "Geo resolver (RSSI)"),
            ("GEO_RESOLVER_GNSS", "Geo resolver (GNSS)"),
            ("GEO_RESOLVER_WIFI", "Geo resolver (WiFi)"),
        ], default="UNKNOWN"
    )

    def __str__(self):
        return f"{self.name}"


class Gateway(models.Model):
    cs_gateway_id=models.CharField(max_length=30) # cs
    name = models.CharField(max_length=30)
    description = models.CharField(max_length=255)
    stats_interval = models.IntegerField() # Cs in seconds
    location = models.ForeignKey(Location, on_delete=models.CASCADE) # Cs
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)
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
        return f"{self.name} - {self.workspace}"
