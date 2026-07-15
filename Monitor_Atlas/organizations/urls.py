from django.urls import path, include

from rest_framework import routers

from . import views

routers = routers.DefaultRouter()

routers.register(r'workspace', views.WorkspaceViewSet)
routers.register(r'tenant', views.TenantViewSet)
routers.register(r'subscription', views.SubscriptionViewSet)

urlpatterns = [
    path('', include(routers.urls)),
]