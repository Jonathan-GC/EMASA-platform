from .models import (
    Ticket,
    Comment,
    Attachment,
    CommentAttachment,
    Notification,
    SupportMembership,
)
from rest_framework import serializers

from users.models import User


class TicketSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), write_only=True, source="user", required=False, allow_null=True
    )

    class Meta:
        model = Ticket
        fields = "__all__"

    def get_user(self, obj):
        user = obj.user
        if user:
            return {
                "id": user.id,
                "username": user.username,
                "full_name": user.get_full_name() or user.username,
                "email": user.email,
            }
        return None

    def validate(self, data):

        if data.get("infrastructure_category") == "Machines":
            machine_type = data.get("machine_type")
            electric_sub = data.get("electric_machine_subtype")
            mechanical_sub = data.get("mechanical_machine_subtype")

            if not machine_type:
                raise serializers.ValidationError("You must select a machine type.")

            if machine_type == "Electric" and not electric_sub:
                raise serializers.ValidationError(
                    "You must select an electric machine subtype."
                )

            if machine_type == "Mechanical" and not mechanical_sub:
                raise serializers.ValidationError(
                    "You must select a mechanical machine subtype."
                )

            if (machine_type == "Electric" and mechanical_sub) or (
                machine_type == "Mechanical" and electric_sub
            ):
                raise serializers.ValidationError(
                    "You cannot select subtypes of both machine types."
                )

        return data


class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = "__all__"


class CommentAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommentAttachment
        fields = "__all__"


class CommentSerializer(serializers.ModelSerializer):
    attachments = CommentAttachmentSerializer(many=True, read_only=True)
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = "__all__"

    def get_user_name(self, obj):
        return obj.user.get_full_name() or obj.user.username


class TicketConversationSerializer(serializers.ModelSerializer):
    """
    Serializer for the complete ticket conversation including:
    - Ticket details
    - Ticket attachments
    - All comments with their attachments (ordered chronologically)
    """

    attachments = AttachmentSerializer(many=True, read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    user_name = serializers.SerializerMethodField()
    assigned_to_name = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = "__all__"

    def get_user_name(self, obj):
        if obj.user:
            return obj.user.get_full_name() or obj.user.username
        elif obj.guest_name:
            return obj.guest_name
        return "Unknown"

    def get_assigned_to_name(self, obj):
        if obj.assigned_to:
            return obj.assigned_to.get_full_name() or obj.assigned_to.username
        return None

    def to_representation(self, instance):
        """
        Override to ensure comments are ordered chronologically
        """
        representation = super().to_representation(instance)
        # Comments are already ordered in the view, but we ensure it here too
        comments = instance.comments.all().order_by("created_at")
        representation["comments"] = CommentSerializer(comments, many=True).data
        return representation


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = "__all__"


class SupportMembershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportMembership
        fields = "__all__"
