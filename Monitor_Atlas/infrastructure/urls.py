from django.urls import path, include

from rest_framework import routers

from . import views

routers = routers.DefaultRouter()

routers.register(r'gateway', views.GatewayViewSet, basename='gateway')
routers.register(r'gateways', views.GatewayViewSet, basename='gateways')
routers.register(r'machine', views.MachineViewSet, basename='machine')
routers.register(r'machines', views.MachineViewSet, basename='machines')
routers.register(r'type', views.TypeViewSet, basename='type')
routers.register(r'types', views.TypeViewSet, basename='types')
routers.register(r'device', views.DeviceViewSet, basename='device')
routers.register(r'devices', views.DeviceViewSet, basename='devices')
routers.register(r'application', views.ApplicationViewSet, basename='application')
routers.register(r'applications', views.ApplicationViewSet, basename='applications')
routers.register(r'location', views.LocationViewSet, basename='location')
routers.register(r'locations', views.LocationViewSet, basename='locations')
routers.register(r'consent', views.DeviceConsentViewSet, basename='consent')
routers.register(r'consents', views.DeviceConsentViewSet, basename='consents')

urlpatterns = [
    path('', include(routers.urls)),
]
