from .models import DeviceProfile, DeviceProfileTemplate, ApiUser, TenantUser
from rest_framework import serializers


class DeviceProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceProfile
        fields = '__all__'


class DeviceProfileTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceProfileTemplate
        fields = '__all__'


class ApiUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApiUser
        fields = '__all__'


class TenantUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = TenantUser
        fields = '__all__'

