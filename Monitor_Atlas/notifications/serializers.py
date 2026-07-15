from rest_framework import serializers
from .models import FCMDevice, Notification, NotificationSettings


class FCMDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = FCMDevice
        fields = "__all__"
        read_only_fields = ["id", "user", "created_at", "updated_at"]

    def create(self, validated_data):
        user = self.context["request"].user
        device, created = FCMDevice.objects.update_or_create(
            user=user,
            fcm_token=validated_data["fcm_token"],
            defaults={"platform": validated_data["platform"], "is_active": True},
        )
        return device


class FCMDeviceRegisterSerializer(serializers.Serializer):
    fcm_token = serializers.CharField(max_length=255)
    platform = serializers.ChoiceField(choices=FCMDevice.PLATFORM_CHOICES)


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = "__all__"
        read_only_fields = ["id", "user", "created_at"]


class NotificationSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationSettings
        fields = "__all__"
        read_only_fields = ["id", "user", "created_at", "updated_at"]
