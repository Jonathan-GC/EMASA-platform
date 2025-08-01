from django.urls import path, include

from rest_framework import routers

from . import views

routers = routers.DefaultRouter()



urlpatterns = [
    path('/api/v1/', include(routers.urls)),
]