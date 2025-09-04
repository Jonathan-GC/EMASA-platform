from django.urls import path, include

from rest_framework import routers

from . import views

routers = routers.DefaultRouter()

routers.register(r'permission-key', views.PermissionKeyViewSet)
routers.register(r'role', views.RoleViewSet)
routers.register(r'workspace-membership', views.WorkspaceMembershipViewSet)
routers.register(r'role-permission', views.RolePermissionViewSet)


urlpatterns = [
    path('', include(routers.urls)),
]