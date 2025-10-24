from django.urls import path, include

from rest_framework import routers

from . import views

routers = routers.DefaultRouter()

routers.register(r"ticket", views.TicketViewSet)
routers.register(r"comment", views.CommentViewSet)
routers.register(r"attachment", views.AttachmentViewSet)
routers.register(r"comment-attachment", views.CommentAttachmentViewSet)
routers.register(r"notification", views.NotificationViewSet)

urlpatterns = [
    path("", include(routers.urls)),
]
