from django.db import models
from organizations.hasher import generate_id


# Create your models here.
class FCMDevice(models.Model):
    id = models.CharField(
        max_length=16, primary_key=True, default=generate_id, editable=False
    )
    PLATFORM_CHOICES = (("android", "Android"), ("ios", "iOS"), ("web", "Web"))
    user = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="fcm_devices"
    )
    fcm_token = models.CharField(max_length=255, unique=True)
    platform = models.CharField(max_length=10, choices=PLATFORM_CHOICES)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Notification(models.Model):
    TOPIC_CHOICES = (
        ("general", "General"),
        ("alerts", "Alerts"),
        ("updates", "Updates"),
    )
    TYPE_CHOICES = (
        ("info", "Info"),
        ("warning", "Warning"),
        ("error", "Error"),
        ("success", "Success"),
    )
    id = models.CharField(
        max_length=16, primary_key=True, default=generate_id, editable=False
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default="info")
    topic = models.CharField(max_length=20, choices=TOPIC_CHOICES, default="general")
    user = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="notifications"
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class NotificationSettings(models.Model):
    id = models.CharField(
        max_length=16, primary_key=True, default=generate_id, editable=False
    )
    user = models.OneToOneField(
        "users.User", on_delete=models.CASCADE, related_name="notification_settings"
    )
    topic_preferences = models.JSONField(
        default=dict, help_text="User's topic preferences for notifications"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
