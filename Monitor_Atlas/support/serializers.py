from .models import Ticket, Comment, Attachment, CommentAttachment, Notification
from rest_framework import serializers


class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = "__all__"

    def validate(self, data):
        if not data.get("user") and (
            not data.get("guest_name") or not data.get("guest_email")
        ):
            raise serializers.ValidationError(
                "Guest tickets must have a name and email address."
            )
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


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = "__all__"


class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = "__all__"


class CommentAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommentAttachment
        fields = "__all__"


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = "__all__"
