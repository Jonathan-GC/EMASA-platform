from django.urls import path, include

from rest_framework import routers

from . import views

routers = routers.DefaultRouter()

routers.register(r'device-profile', views.DeviceProfileViewSet)
routers.register(r'device-profile-template', views.DeviceProfileTemplateViewSet)
routers.register(r'api-user', views.ApiUserViewSet)


urlpatterns = [
    path('', include(routers.urls)),
]
