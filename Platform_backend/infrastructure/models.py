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
    api_id=models.CharField(max_length=30) # chirpstack
    name = models.CharField(max_length=30)
    device_type = models.ForeignKey(Type, on_delete=models.CASCADE, help_text="You can classify devices by type and set a custom icon") # icon, classification and such
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.api_id} - {self.name}"
    
class Device(models.Model):
    name = models.CharField(max_length=30)
    description = models.CharField(max_length=255)
    device_eui = models.CharField(max_length=16, help_text="Device EUI (Chirpstack)") # chirpstack
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)
    device_type = models.ForeignKey(Type, on_delete=models.CASCADE) # icon, classification and such
    device_profile = models.ForeignKey(DeviceProfile, on_delete=models.CASCADE, help_text="Device profile (Chirpstack)") # chirpstack
    application = models.ForeignKey(Application, on_delete=models.CASCADE, help_text="Application (Chirpstack)") # chirpstack

    def __str__(self):
        return f"{self.api_id} - {self.name}"

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
    api_id=models.CharField(max_length=30) # chirpstack
    name = models.CharField(max_length=30)
    description = models.CharField(max_length=255)
    stats_interval = models.IntegerField() # Chirpstack in seconds
    location = models.ForeignKey(Location, on_delete=models.CASCADE) # Chirpstack
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.name} - {self.workspace}"
