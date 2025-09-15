from .models import Workspace, Tenant, Subscription
from rest_framework import serializers


class WorkspaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workspace
        fields = "__all__"


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = "__all__"


class TenantSerializer(serializers.ModelSerializer):
    subscription = serializers.SerializerMethodField(read_only=True)
    subscription_id = serializers.PrimaryKeyRelatedField(
        queryset=Subscription.objects.all(), write_only=True, source="subscription"
    )

    class Meta:
        model = Tenant
        fields = "__all__"

    def get_subscription(self, obj):
        subscription = obj.subscription
        if subscription:
            return {
                "id": subscription.id,
                "name": subscription.name,
                "can_have_gateways": subscription.can_have_gateways,
                "max_device_count": subscription.max_device_count,
                "max_gateway_count": subscription.max_gateway_count,
            }
        return None
