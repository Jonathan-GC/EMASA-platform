from django.urls import path, include

from rest_framework import routers

from . import views

routers = routers.DefaultRouter()

routers.register(r"role", views.RoleViewSet)
routers.register(r"workspace-membership", views.WorkspaceMembershipViewSet)


urlpatterns = [
    path("", include(routers.urls)),
]
