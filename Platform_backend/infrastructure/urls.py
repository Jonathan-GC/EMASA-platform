from django.urls import path, include

from rest_framework import routers

from . import views

routers = routers.DefaultRouter()

routers.register(r'gateway', views.GatewayViewSet)
routers.register(r'machine', views.MachineViewSet)
routers.register(r'node-type', views.NodeTypeViewSet)
routers.register(r'node', views.NodeViewSet)
routers.register(r'service', views.ServiceViewSet)

urlpatterns = [
    path('/api/v1/', include(routers.urls)),
]
