from rest_framework import viewsets
from .models import (
    Ticket,
    Comment,
    Attachment,
    CommentAttachment,
    Notification,
    SupportMembership,
)
from .serializers import (
    TicketSerializer,
    CommentSerializer,
    AttachmentSerializer,
    CommentAttachmentSerializer,
    NotificationSerializer,
    SupportMembershipSerializer,
)

from rest_framework.decorators import action
from loguru import logger
from drf_spectacular.utils import extend_schema_view, extend_schema
from rest_framework.response import Response

from .models import (
    CATEGORY_CHOICES,
    MACHINE_TYPE_CHOICES,
    ELECTRIC_MACHINE_CHOICES,
    MECHANICAL_MACHINE_CHOICES,
    INFRASTRUCTURE_CATEGORY_CHOICES,
)


# Create your views here.
@extend_schema_view(
    list=extend_schema(description="Ticket List"),
    create=extend_schema(description="Ticket Create"),
    retrieve=extend_schema(description="Ticket Retrieve"),
    update=extend_schema(description="Ticket Update"),
    partial_update=extend_schema(description="Ticket Partial Update"),
    destroy=extend_schema(description="Ticket Destroy"),
    get_all_types=extend_schema(description="Get all classification types"),
)
class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer

    def perform_create(self, serializer):
        support_member = SupportMembership.objects.filter(
            role="support_manager"
        ).first()
        user = support_member.user
        ticket = serializer.save()
        ticket_number = f"TICKET-{ticket.id}"
        notification = Notification.objects.create(
            title="New Ticket Submitted",
            message=f"Ticket {ticket_number} has been created.",
            type="warning",
            user=user,
        )
        notification.save()
        notification.notify_ws()
        return ticket

    @action(detail=False, methods=["get"], description="Get all classification types")
    def get_all_types(self, request):
        return Response(
            {
                "categories": dict(CATEGORY_CHOICES),
                "infrastructure_categories": dict(INFRASTRUCTURE_CATEGORY_CHOICES),
                "machine_types": dict(MACHINE_TYPE_CHOICES),
                "electric_machine_subtypes": dict(ELECTRIC_MACHINE_CHOICES),
                "mechanical_machine_subtypes": dict(MECHANICAL_MACHINE_CHOICES),
            }
        )


@extend_schema_view(
    list=extend_schema(description="Comment List"),
    create=extend_schema(description="Comment Create"),
    retrieve=extend_schema(description="Comment Retrieve"),
    update=extend_schema(description="Comment Update"),
    partial_update=extend_schema(description="Comment Partial Update"),
    destroy=extend_schema(description="Comment Destroy"),
)
class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer


@extend_schema_view(
    list=extend_schema(description="Attachment List"),
    create=extend_schema(description="Attachment Create"),
    retrieve=extend_schema(description="Attachment Retrieve"),
    update=extend_schema(description="Attachment Update"),
    partial_update=extend_schema(description="Attachment Partial Update"),
    destroy=extend_schema(description="Attachment Destroy"),
)
class AttachmentViewSet(viewsets.ModelViewSet):
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer


@extend_schema_view(
    list=extend_schema(description="Comment Attachment List"),
    create=extend_schema(description="Comment Attachment Create"),
    retrieve=extend_schema(description="Comment Attachment Retrieve"),
    update=extend_schema(description="Comment Attachment Update"),
    partial_update=extend_schema(description="Comment Attachment Partial Update"),
    destroy=extend_schema(description="Comment Attachment Destroy"),
)
class CommentAttachmentViewSet(viewsets.ModelViewSet):
    queryset = CommentAttachment.objects.all()
    serializer_class = CommentAttachmentSerializer


@extend_schema_view(
    list=extend_schema(description="Notification List"),
    create=extend_schema(description="Notification Create"),
    retrieve=extend_schema(description="Notification Retrieve"),
    update=extend_schema(description="Notification Update"),
    partial_update=extend_schema(description="Notification Partial Update"),
    destroy=extend_schema(description="Notification Destroy"),
    notify_user=extend_schema(description="Notify user via WebSocket"),
    my_notifications=extend_schema(description="Get user's notifications"),
    mark_as_read=extend_schema(description="Mark notification as read"),
)
class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer

    @action(
        detail=True,
        methods=["post"],
        description="Notify user via WebSocket",
    )
    def notify_user(self, request, pk=None):
        notification = self.get_object()
        try:
            notification.notify_ws()
        except Exception as e:
            logger.error(f"Failed to notify user: {e}")
            return Response({"status": "failed", "error": str(e)}, status=500)

        return Response({"status": "notified"})

    @action(
        detail=False,
        methods=["get"],
        description="Get user's notifications",
    )
    def my_notifications(self, request):
        user = request.user
        notifications = Notification.objects.filter(user=user).order_by("-created_at")
        page = self.paginate_queryset(notifications)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(notifications, many=True)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=["post"],
        description="Mark notification as read",
    )
    def mark_as_read(self, request, pk=None):
        notification = self.get_object()
        try:
            notification.mark_as_read()
        except Exception as e:
            logger.error(f"Failed to mark notification as read: {e}")
            return Response({"status": "failed", "error": str(e)}, status=500)

        return Response({"status": "marked_as_read"})
