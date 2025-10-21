from rest_framework import viewsets
from .models import Ticket, Comment, Attachment, CommentAttachment, Notification
from .serializers import (
    TicketSerializer,
    CommentSerializer,
    AttachmentSerializer,
    CommentAttachmentSerializer,
    NotificationSerializer,
)

from rest_framework.decorators import action
from loguru import logger
from drf_spectacular.utils import extend_schema_view, extend_schema
from rest_framework.response import Response

from roles.permissions import HasPermission

from django_tenants.utils import get_tenant
from guardian.shortcuts import get_objects_for_user
from roles.helpers import assign_object_permissions


# Create your views here.
@extend_schema_view(
    list=extend_schema(description="Ticket List"),
    create=extend_schema(description="Ticket Create"),
    retrieve=extend_schema(description="Ticket Retrieve"),
    update=extend_schema(description="Ticket Update"),
    partial_update=extend_schema(description="Ticket Partial Update"),
    destroy=extend_schema(description="Ticket Destroy"),
)
class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    permission_classes = [HasPermission]
    scope = "ticket"

    def get_queryset(self):
        user = self.request.user

        if user.is_superuser:
            return Ticket.objects.all()

        queryset = get_objects_for_user(
            user, "view_ticket_details", klass=Ticket, accept_global_perms=False
        )

        try:
            current_tenant = get_tenant()
            queryset = queryset.filter(workspace__tenant=current_tenant)
        except Exception as e:
            logger.error(f"Error getting current tenant: {e}")

        return queryset

    def perform_create(self, serializer):
        instance = serializer.save()

        assign_object_permissions(
            self.request.user,
            instance,
            permissions=["view", "change", "delete", "manage"],
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
    permission_classes = [HasPermission]
    scope = "comment"

    def get_queryset(self):
        user = self.request.user

        if user.is_superuser:
            return Comment.objects.all()

        queryset = get_objects_for_user(
            user, "view_comment_details", klass=Comment, accept_global_perms=False
        )

        try:
            current_tenant = get_tenant()
            queryset = queryset.filter(ticket__workspace__tenant=current_tenant)
        except Exception as e:
            logger.error(f"Error getting current tenant: {e}")

        return queryset

    def perform_create(self, serializer):
        instance = serializer.save()

        assign_object_permissions(
            self.request.user,
            instance,
            permissions=["view", "change", "delete", "manage"],
        )


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
    permission_classes = [HasPermission]
    scope = "attachment"

    def get_queryset(self):
        user = self.request.user

        if user.is_superuser:
            return Attachment.objects.all()

        queryset = get_objects_for_user(
            user,
            "view_attachment_details",
            klass=Attachment,
            accept_global_perms=False,
        )
        try:
            current_tenant = get_tenant()
            queryset = queryset.filter(ticket__workspace__tenant=current_tenant)
        except Exception as e:
            logger.error(f"Error getting current tenant: {e}")

        return queryset

    def perform_create(self, serializer):
        instance = serializer.save()

        assign_object_permissions(
            self.request.user,
            instance,
            permissions=["view", "change", "delete", "manage"],
        )


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
    permission_classes = [HasPermission]
    scope = "comment_attachment"

    def get_queryset(self):
        user = self.request.user

        if user.is_superuser:
            return CommentAttachment.objects.all()

        queryset = get_objects_for_user(
            user,
            "view_comment_attachment_details",
            klass=CommentAttachment,
            accept_global_perms=False,
        )
        try:
            current_tenant = get_tenant()
            queryset = queryset.filter(
                comment__ticket__workspace__tenant=current_tenant
            )
        except Exception as e:
            logger.error(f"Error getting current tenant: {e}")

        return queryset

    def perform_create(self, serializer):
        instance = serializer.save()

        assign_object_permissions(
            self.request.user,
            instance,
            permissions=["view", "change", "delete", "manage"],
        )


@extend_schema_view(
    list=extend_schema(description="Notification List"),
    create=extend_schema(description="Notification Create"),
    retrieve=extend_schema(description="Notification Retrieve"),
    update=extend_schema(description="Notification Update"),
    partial_update=extend_schema(description="Notification Partial Update"),
    destroy=extend_schema(description="Notification Destroy"),
    notify_user=extend_schema(description="Notify user via WebSocket"),
    my_notifications=extend_schema(description="Get user's notifications"),
)
class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [HasPermission]
    scope = "notification"

    def get_queryset(self):
        user = self.request.user

        if user.is_superuser:
            return Notification.objects.all()

        queryset = get_objects_for_user(
            user,
            "view_notification_details",
            klass=Notification,
            accept_global_perms=False,
        )

        return queryset

    def perform_create(self, serializer):
        instance = serializer.save()

        assign_object_permissions(
            self.request.user,
            instance,
            permissions=["view", "change", "delete", "manage"],
        )

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
