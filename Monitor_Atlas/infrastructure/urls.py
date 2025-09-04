from django.urls import path, include

from rest_framework import routers

from . import views

routers = routers.DefaultRouter()

routers.register(r'gateway', views.GatewayViewSet)
routers.register(r'machine', views.MachineViewSet)
routers.register(r'type', views.TypeViewSet)
routers.register(r'device', views.DeviceViewSet)
routers.register(r'application', views.ApplicationViewSet)
routers.register(r'location', views.LocationViewSet)

urlpatterns = [
    path('', include(routers.urls)),
]
