from django.contrib import admin

from .models import FCMDevice, Notification, NotificationSettings


@admin.register(FCMDevice)
class FCMDeviceAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "platform", "is_active", "created_at"]
    list_filter = ["platform", "is_active"]
    search_fields = ["user__username", "fcm_token"]


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["id", "title", "type", "topic", "user", "is_read", "created_at"]
    list_filter = ["type", "topic", "is_read"]
    search_fields = ["title", "message", "user__username"]


@admin.register(NotificationSettings)
class NotificationSettingsAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "created_at", "updated_at"]
    search_fields = ["user__username"]
