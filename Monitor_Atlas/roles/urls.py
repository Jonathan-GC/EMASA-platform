from django.urls import path, include

from rest_framework import routers

from . import views

routers = routers.DefaultRouter()

routers.register(r"role", views.RoleViewSet)
routers.register(r"workspace-membership", views.WorkspaceMembershipViewSet)


urlpatterns = [
    path("catalog/", views.RoleViewSet.as_view({"get": "catalog"}), name="role-catalog-direct"),
    path("", include(routers.urls)),
]
