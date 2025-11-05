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
    TicketConversationSerializer,
)

from rest_framework.decorators import action
from loguru import logger
from drf_spectacular.utils import extend_schema_view, extend_schema
from rest_framework.response import Response

from .models import (
    PRIORITY_CHOICES,
    STATUS_CHOICES,
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
        if not support_member:
            logger.error(
                "No support member with role 'support_manager' found. If in development, please run initial setup."
            )
            raise Exception(
                "Support manager not found. If in development, please run initial setup."
            )
        user = support_member.user
        ticket = serializer.save()
        if ticket.organization:
            ticket_body = f"{ticket.organization} submitted a Ticket."
        else:
            ticket_body = f"Ticket {ticket_number} has been submitted."

        ticket_number = f"TICKET-{ticket.id}"
        notification = Notification.objects.create(
            title="New Ticket Submitted",
            message=ticket_body,
            type="warning",
            user=user,
        )
        notification.save()
        notification.notify_ws()
        return ticket

    @action(detail=True, methods=["get"], description="Get ticket conversation")
    def conversation(self, request, pk=None):
        """
        Returns the complete conversation for a ticket including:
        - Ticket details
        - All ticket attachments
        - All comments (ordered chronologically) with their attachments
        - The 'response' flag in each comment indicates if it's from the technician (True) or user (False)
        """
        ticket = self.get_object()

        # Prefetch related data to optimize queries
        ticket = Ticket.objects.prefetch_related(
            "attachments", "comments__attachments", "comments__user"
        ).get(pk=ticket.pk)

        serializer = TicketConversationSerializer(ticket)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], description="Delegate the ticket")
    def delegate(self, request, pk=None):
        ticket = self.get_object()
        assigned_to_id = request.data.get("assigned_to_id")
        if not assigned_to_id:
            return Response({"error": "assigned_to_id is required."}, status=400)

        try:
            assigned_user = User.objects.get(id=assigned_to_id)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=404)

    @action(detail=False, methods=["get"], description="Get support members")
    def get_support_members(self, request):
        support_members = SupportMembership.objects.select_related("user").all()
        data = [
            {
                "id": member.user.id,
                "full_name": member.user.get_full_name() or member.user.username,
                "role": member.role,
            }
            for member in support_members
        ]
        return Response(data)

    @action(detail=False, methods=["get"], description="Get all classification types")
    def get_all_types(self, request):
        return Response(
            {
                "priority_levels": dict(PRIORITY_CHOICES),
                "status_types": dict(STATUS_CHOICES),
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


@extend_schema_view(
    list=extend_schema(description="Support Membership List"),
    create=extend_schema(description="Support Membership Create"),
    retrieve=extend_schema(description="Support Membership Retrieve"),
    update=extend_schema(description="Support Membership Update"),
    partial_update=extend_schema(description="Support Membership Partial Update"),
    destroy=extend_schema(description="Support Membership Destroy"),
)
class SupportMembershipViewSet(viewsets.ModelViewSet):
    queryset = SupportMembership.objects.all()
    serializer_class = SupportMembershipSerializer
