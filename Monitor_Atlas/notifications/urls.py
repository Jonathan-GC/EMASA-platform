from django.urls import path, include

from rest_framework import routers

from . import views

router = routers.DefaultRouter()

router.register(r"devices", views.FCMDeviceViewSet, basename="fcm-device")
router.register(r"settings", views.NotificationSettingsViewSet, basename="notification-settings")
router.register(r"notifications", views.NotificationViewSet, basename="notification")

urlpatterns = [
    path("", include(router.urls)),
]
