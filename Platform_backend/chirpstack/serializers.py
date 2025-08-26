from .models import DeviceProfile, DeviceProfileTemplate, ApiUser
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
