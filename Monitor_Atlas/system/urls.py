from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AppsModelsView,
    SystemHealthView,
    HermesHealthView,
    AtlasHealthView,
    DatabaseBackupViewSet,
)

router = DefaultRouter()
router.register(r"backups", DatabaseBackupViewSet, basename="database-backup")

urlpatterns = [
    path("apps/", AppsModelsView.as_view(), name="system-apps"),
    path("models/", AppsModelsView.as_view(), name="system-models"),
    path("health/", SystemHealthView.as_view(), name="system-health"),
    path("health/hermes/", HermesHealthView.as_view(), name="system-health-hermes"),
    path("health/atlas/", AtlasHealthView.as_view(), name="system-health-atlas"),
    path("", include(router.urls)),
]

