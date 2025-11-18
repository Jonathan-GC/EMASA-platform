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
from guardian.shortcuts import get_users_with_perms

from roles.permissions import IsServiceOrHasPermission

from infrastructure.models import Device
from users.models import User

from rest_framework.decorators import action
from loguru import logger
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiExample
from rest_framework.response import Response

from .models import (
    PRIORITY_CHOICES,
    STATUS_CHOICES,
    CATEGORY_CHOICES,
    MACHINE_TYPE_CHOICES,
    ELECTRIC_MACHINE_CHOICES,
    MECHANICAL_MACHINE_CHOICES,
    INFRASTRUCTURE_CATEGORY_CHOICES,
    SUPPORT_MEMBERSHIP_ROLE_CHOICES,
)

from roles.helpers import support_manager_can_view_all_support_members

from users.emails import (
    send_ticket_created_notification_email,
    send_ticket_updated_notification_email,
    send_ticket_updated_notification_email_to_staff,
    send_new_ticket_notification_email_to_staff,
)

from users.jwt import generate_token


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
    alert=extend_schema(
        description="Alert",
        examples=[
            OpenApiExample(
                "Alert Example",
                summary="Alert Example",
                description="Example payload for sending an alert notification.",
                value={
                    "title": "Device Offline",
                    "message": "The device with ID 12345 has gone offline.",
                    "type": "error",
                    "device_id": 1,
                },
                request_only=True,
                response_only=False,
            )
        ],
    ),
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

    @action(
        detail=False,
        methods=["post"],
        description="Alert",
        permission_classes=[IsServiceOrHasPermission],
    )
    def alert(self, request):
        required_fields = ["title", "message", "type", "dev_eui"]
        data = request.data
        device = Device.objects.filter(dev_eui=data.get("dev_eui")).first()
        if not device:
            logger.error(f"Device with ID {data.get('dev_eui')} not found.")
            return Response({"error": "Device not found."}, status=404)

        users = get_users_with_perms(device, only_with_perms_in=["view_device"])
        superuser = User.objects.filter(is_superuser=True).first()
        if not users and not superuser:
            logger.error(
                f"No users found with permission to view device with ID {data.get('device_id')}."
            )
            return Response(
                {"error": "No users found with permission to view this device."},
                status=404,
            )
        for user in users:
            notification = Notification.objects.create(
                title=data.get("title"),
                message=data.get("message"),
                type=data.get("type"),
                user=user,
            )
            notification.save()
            try:
                notification.notify_ws()
            except Exception as e:
                logger.error(f"Failed to notify user {user.id}: {e}")

        if superuser and superuser not in users:
            notification = Notification.objects.create(
                title=data.get("title"),
                message=data.get("message"),
                type=data.get("type"),
                user=superuser,
            )
            notification.save()
            try:
                notification.notify_ws()
            except Exception as e:
                logger.error(f"Failed to notify superuser {superuser.id}: {e}")

        return Response({"status": "alert_sent"}, status=200)


@extend_schema_view(
    list=extend_schema(description="Ticket List"),
    create=extend_schema(description="Ticket Create"),
    retrieve=extend_schema(description="Ticket Retrieve"),
    update=extend_schema(description="Ticket Update"),
    partial_update=extend_schema(description="Ticket Partial Update"),
    destroy=extend_schema(description="Ticket Destroy"),
    get_all_types=extend_schema(description="Get all classification types"),
    get_support_members=extend_schema(description="Get support members"),
    delegate=extend_schema(
        description="Delegate the ticket",
        examples=[
            OpenApiExample(
                "Delegate Ticket Example",
                summary="Delegate Ticket Example",
                description="Example payload for delegating a ticket to a support member.",
                value={"assigned_to_id": 2},
                request_only=True,
                response_only=False,
            ),
        ],
    ),
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
        ticket = serializer.save(assigned_to=user)
        ticket_number = f"TICKET-{ticket.id}"
        if ticket.organization:
            ticket_body = f"{ticket.organization} submitted a Ticket."
        else:
            ticket_body = f"Ticket {ticket_number} has been submitted."

        notification = Notification.objects.create(
            title="New Ticket Submitted",
            message=ticket_body,
            type="warning",
            user=user,
        )
        notification.notify_ws()

        if not ticket.user:
            token = generate_token(
                scope="ticket_access", expires_minutes=60 * 24 * 3, ticket_id=ticket.id
            )  # 3 days validity
            ticket_user_name = ticket.guest_name
            ticket_user_email = ticket.guest_email
        else:
            token = generate_token(
                user_id=ticket.user.id,
                scope="ticket_access",
                expires_minutes=60 * 24 * 3,
                ticket_id=ticket.id,
            )  # 3 days validity
            ticket_user = User.objects.get(id=ticket.user.id)
            ticket_user_name = ticket_user.get_full_name() or ticket_user.username
            ticket_user_email = ticket_user.email

        send_ticket_created_notification_email(
            name=ticket_user_name,
            email=ticket_user_email,
            ticket=ticket,
            token=token,
        )

        send_new_ticket_notification_email_to_staff(
            staff_email=user.email,
            ticket=ticket,
            comment=None,
        )

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

        ticket = Ticket.objects.prefetch_related(
            "attachments", "comments__attachments", "comments__user"
        ).get(pk=ticket.pk)

        serializer = TicketConversationSerializer(ticket)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], description="Mark ticket as read")
    def mark_as_read(self, request, pk=None):
        ticket = self.get_object()
        ticket.is_read = True
        ticket.save()
        return Response({"status": "ticket_marked_as_read"})

    @action(detail=True, methods=["post"], description="Delegate the ticket")
    def delegate(self, request, pk=None):
        ticket = self.get_object()
        assigned_to_id = request.data.get("assigned_to_id")
        if not assigned_to_id:
            return Response({"error": "assigned_to_id is required."}, status=400)

        try:
            assigned_user = User.objects.get(id=assigned_to_id)
            ticket.assigned_to = assigned_user
            ticket.is_read = False
            ticket.save()
            notification = Notification.objects.create(
                title="New Ticket Assignment",
                message=f"The ticket '{ticket.title}' has been delegated to you.",
                type="info",
                user=assigned_user,
            )
            notification.save()
            notification.notify_ws()
            return Response({"status": "ticket_delegated"})

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
                "support_membership_roles": dict(SUPPORT_MEMBERSHIP_ROLE_CHOICES),
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

    def perform_create(self, serializer):
        instance = serializer.save()
        user = instance.user
        support_managers = SupportMembership.objects.filter(role="support_manager")
        support_managers_count = support_managers.count()
        if support_managers_count > 1:
            for support_manager in support_managers:
                support_manager_can_view_all_support_members(
                    support_manager=support_manager, user=user
                )
        elif support_managers_count == 1:
            support_manager = support_managers.first()
            support_manager_can_view_all_support_members(
                support_manager=support_manager, user=user
            )
        return instance
