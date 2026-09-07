from django.urls import path, include

from rest_framework import routers

from . import views

routers = routers.DefaultRouter()

routers.register(r"ticket", views.TicketViewSet, basename="ticket")
routers.register(r"tickets", views.TicketViewSet, basename="tickets")
routers.register(r"comment", views.CommentViewSet, basename="comment")
routers.register(r"comments", views.CommentViewSet, basename="comments")
routers.register(r"attachment", views.AttachmentViewSet, basename="attachment")
routers.register(r"attachments", views.AttachmentViewSet, basename="attachments")
routers.register(r"comment-attachment", views.CommentAttachmentViewSet, basename="comment-attachment")
routers.register(r"comment-attachments", views.CommentAttachmentViewSet, basename="comment-attachments")
routers.register(r"support_membership", views.SupportMembershipViewSet, basename="support_membership")
routers.register(r"support-memberships", views.SupportMembershipViewSet, basename="support-memberships")
routers.register(r"technician-assignments", views.TechnicianAssignmentViewSet, basename="technician-assignments")
routers.register(r"diagnostic-passes", views.TechnicianAssignmentViewSet, basename="diagnostic-passes")

urlpatterns = [
    path("", include(routers.urls)),
]
