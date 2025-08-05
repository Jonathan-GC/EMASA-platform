from django.urls import path, include

from rest_framework import routers

from . import views

routers = routers.DefaultRouter()

routers.register(r'workspace', views.WorkspaceViewSet)
routers.register(r'organization', views.OrganizationViewSet)
routers.register(r'region', views.RegionViewSet)

urlpatterns = [
    path('api/v1/', include(routers.urls)),
]