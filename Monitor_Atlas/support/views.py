from rest_framework import viewsets
from .models import Ticket, Comment, Attachment, CommentAttachment, Notification
from .serializers import (
    TicketSerializer,
    CommentSerializer,
    AttachmentSerializer,
    CommentAttachmentSerializer,
    NotificationSerializer,
)

import logging
from drf_spectacular.utils import extend_schema_view, extend_schema


# Create your views here.
@extend_schema_view(
    list=extend_schema(description="Ticket List"),
    create=extend_schema(description="Ticket Create"),
    retrieve=extend_schema(description="Ticket Retrieve"),
    update=extend_schema(description="Ticket Update"),
    partial_update=extend_schema(description="Ticket Partial Update"),
    destroy=extend_schema(description="Ticket Destroy"),
)
class TickeViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer


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
)
class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
