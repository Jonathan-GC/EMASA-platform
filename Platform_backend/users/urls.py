from django.urls import path, include

from rest_framework import routers

from . import views

routers = routers.DefaultRouter()

routers.register(r'user', views.UserViewSet)

urlpatterns = [
    path('api/v1/', include(routers.urls)),
]