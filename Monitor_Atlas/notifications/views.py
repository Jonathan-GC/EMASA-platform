from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiExample,
    OpenApiParameter,
)
from loguru import logger

from .models import FCMDevice, Notification, NotificationSettings
from .serializers import (
    FCMDeviceSerializer,
    FCMDeviceRegisterSerializer,
    NotificationSerializer,
    NotificationSettingsSerializer,
)
from .engine import NotificationsEngine
from .helpers import get_users_for_device
from roles.permissions import IsServiceOrHasPermission, IsOwnerOrAdmin

_PARAM_USER_ID = OpenApiParameter(
    name="user_id",
    description="Filter by user ID (admin/debug only)",
    required=False,
    type=str,
)


@extend_schema_view(
    list=extend_schema(
        description="List FCM Devices",
        parameters=[_PARAM_USER_ID],
    ),
    create=extend_schema(description="Create FCM Device"),
    retrieve=extend_schema(description="Retrieve FCM Device"),
    partial_update=extend_schema(description="Patch FCM Device"),
    destroy=extend_schema(description="Unregister FCM Device"),
    register=extend_schema(
        description="Register FCM Device",
        examples=[
            OpenApiExample(
                "Register device",
                value={"fcm_token": "abc123token", "platform": "android"},
                request_only=True,
            )
        ],
    ),
    unregister=extend_schema(
        description="Unregister (deactivate) FCM Device",
    ),
)
class FCMDeviceViewSet(viewsets.ModelViewSet):
    serializer_class = FCMDeviceSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            user_id = self.request.query_params.get("user_id")
            if user_id:
                return FCMDevice.objects.filter(user_id=user_id)
        return FCMDevice.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=["post"])
    def register(self, request):
        register_serializer = FCMDeviceRegisterSerializer(data=request.data)
        register_serializer.is_valid(raise_exception=True)

        device, _created = FCMDevice.objects.update_or_create(
            user=request.user,
            fcm_token=register_serializer.validated_data["fcm_token"],
            defaults={
                "platform": register_serializer.validated_data["platform"],
                "is_active": True,
            },
        )

        output = FCMDeviceSerializer(device, context={"request": request})
        status_code = status.HTTP_201_CREATED if _created else status.HTTP_200_OK
        return Response(output.data, status=status_code)

    @action(detail=True, methods=["post"])
    def unregister(self, request, pk=None):
        device = self.get_object()
        device.is_active = False
        device.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(
    list=extend_schema(
        description="List notification settings",
        parameters=[_PARAM_USER_ID],
    ),
    partial_update=extend_schema(description="Update notification settings"),
)
class NotificationSettingsViewSet(
    viewsets.mixins.ListModelMixin,
    viewsets.mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = NotificationSettingsSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            user_id = self.request.query_params.get("user_id")
            if user_id:
                return NotificationSettings.objects.filter(user_id=user_id)
        return NotificationSettings.objects.filter(user=user)

    def get_object(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            user_id = self.request.query_params.get("user_id")
            if user_id:
                from django.shortcuts import get_object_or_404
                from users.models import User

                target_user = get_object_or_404(User, id=user_id)
                obj, _created = NotificationSettings.objects.get_or_create(
                    user=target_user,
                    defaults={
                        "topic_preferences": {
                            "alerts": True,
                            "updates": True,
                            "general": True,
                        }
                    },
                )
                self.check_object_permissions(self.request, obj)
                return obj

        obj, _created = NotificationSettings.objects.get_or_create(
            user=user,
            defaults={
                "topic_preferences": {"alerts": True, "updates": True, "general": True}
            },
        )
        return obj

    def list(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(
        description="List user's notifications",
        parameters=[_PARAM_USER_ID],
    ),
    retrieve=extend_schema(description="Retrieve notification"),
    partial_update=extend_schema(description="Patch notification"),
    destroy=extend_schema(description="Delete a notification"),
    my_notifications=extend_schema(
        description="My notifications",
        parameters=[_PARAM_USER_ID],
    ),
    mark_as_read=extend_schema(description="Mark as read"),
    alert=extend_schema(
        description="Alert endpoint for external services (Hermes)",
        examples=[
            OpenApiExample(
                "Alert example",
                value={
                    "title": "Device Offline",
                    "message": "The device has gone offline.",
                    "type": "error",
                    "dev_eui": "abc123",
                },
                request_only=True,
            )
        ],
    ),
)
class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            user_id = self.request.query_params.get("user_id")
            if user_id:
                return Notification.objects.filter(user_id=user_id)
        return Notification.objects.filter(user=user)

    @action(detail=False, methods=["get"])
    def my_notifications(self, request):
        notifications = self.get_queryset().order_by("-created_at")
        page = self.paginate_queryset(notifications)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(notifications, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def mark_as_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({"status": "marked_as_read"})

    @action(
        detail=False,
        methods=["post"],
        permission_classes=[IsServiceOrHasPermission],
    )
    def alert(self, request):
        required_fields = ["title", "message", "type", "dev_eui"]
        data = request.data
        for field in required_fields:
            if field not in data:
                return Response({"error": f"'{field}' is required."}, status=400)

        try:
            users = get_users_for_device(data["dev_eui"])
        except ValueError as e:
            return Response({"error": str(e)}, status=404)

        results = NotificationsEngine.send_notification(
            users=users,
            title=data["title"],
            message=data["message"],
            type=data["type"],
            topic="alerts",
            extra_data={"dev_eui": data["dev_eui"]},
        )

        if not results["notified"]:
            return Response(
                {
                    "status": "alert_processed",
                    "notified": 0,
                    "skipped": results["skipped"],
                },
                status=200,
            )

        return Response(
            {
                "status": "alert_sent",
                "notified": results["notified"],
                "skipped": results["skipped"],
            },
            status=200,
        )
