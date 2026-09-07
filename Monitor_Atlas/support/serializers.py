from .models import (
    Ticket,
    Comment,
    Attachment,
    CommentAttachment,
    SupportMembership,
    TechnicianAssignment,
)
from rest_framework import serializers

from users.models import User


class TicketSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        write_only=True,
        source="user",
        required=False,
        allow_null=True,
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

        workspace = data.get("workspace")
        tenant = data.get("tenant")
        if self.instance:
            if not workspace and "workspace" not in data:
                workspace = self.instance.workspace
            if not tenant and "tenant" not in data:
                tenant = self.instance.tenant

        if workspace and tenant and workspace.tenant_id != tenant.id:
            raise serializers.ValidationError(
                {"workspace": "The selected workspace does not belong to the ticket's tenant."}
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
        if not obj.user:
            return obj.guest_name
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


class SupportMembershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportMembership
        fields = "__all__"


class TechnicianAssignmentSerializer(serializers.ModelSerializer):
    is_valid = serializers.SerializerMethodField(read_only=True)
    technician_name = serializers.SerializerMethodField(read_only=True)
    workspace_name = serializers.SerializerMethodField(read_only=True)
    ticket_title = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = TechnicianAssignment
        fields = "__all__"

    def get_is_valid(self, obj):
        return obj.is_valid()

    def get_technician_name(self, obj):
        return (obj.technician.get_full_name() or obj.technician.username) if obj.technician else None

    def get_workspace_name(self, obj):
        return obj.workspace.name if obj.workspace else None

    def get_ticket_title(self, obj):
        return obj.ticket.title if obj.ticket else None

    def validate(self, data):
        workspace = data.get("workspace")
        ticket = data.get("ticket")
        if workspace and ticket and ticket.tenant and workspace.tenant_id != ticket.tenant_id:
            raise serializers.ValidationError(
                {"workspace": "Target workspace does not belong to the ticket's tenant."}
            )
        return data
