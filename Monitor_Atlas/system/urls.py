from django.urls import path
from .views import (
    AppsModelsView,
    SystemHealthView,
    HermesHealthView,
    AtlasHealthView,
)

urlpatterns = [
    path("apps/", AppsModelsView.as_view(), name="system-apps"),
    path("models/", AppsModelsView.as_view(), name="system-models"),
    path("health/", SystemHealthView.as_view(), name="system-health"),
    path("health/hermes/", HermesHealthView.as_view(), name="system-health-hermes"),
    path("health/atlas/", AtlasHealthView.as_view(), name="system-health-atlas"),
]
