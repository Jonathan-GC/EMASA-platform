from rest_framework import serializers
from django.core.validators import validate_email
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from roles.models import WorkspaceMembership
from .models import User


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        membership = (
            WorkspaceMembership.objects.filter(user=user)
            .select_related("workspace__tenant")
            .first()
        )
        is_superuser = user.is_superuser

        if membership and membership.workspace and membership.workspace.tenant:
            tenant = membership.workspace.tenant
            cs_tenant_id = getattr(tenant, "cs_tenant_id", None)
            if tenant.name == "EMASA":
                is_global = True
            else:
                is_global = False
        else:
            is_global = False
            cs_tenant_id = None

        token["user_id"] = user.id
        token["username"] = user.username
        token["is_global"] = is_global
        token["cs_tenant_id"] = cs_tenant_id
        token["is_superuser"] = is_superuser

        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        return data


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "code",
            "username",
            "email",
            "name",
            "last_name",
            "is_active",
            "is_staff",
            "is_superuser",
            "phone",
            "address",
        ]

    def validate_username(self, value):
        """
        Validates the username field to ensure that the username is unique
        and has a minimum length requirement. Raises a ValidationError if
        the username already exists in the database or if its length is
        less than 4 characters.
        """
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("This username already exists.")
        if len(value) < 4:
            raise serializers.ValidationError(
                "The username must be at least 4 characters long."
            )
        return value

    def validate_name_and_last_name(self, value):
        """
        Validates that the name and last name contain only letters.
        Raises a ValidationError if any of them contain numbers or special characters.
        """
        user = User.objects.filter(username=value)
        if not user.name.isalpha() or not user.last_name.isalpha():
            raise serializers.ValidationError(
                "First name, middle name or last name must contain only letters."
            )
        return value

    def validate_phone(self, value):
        """
        Validates the phone number field to ensure that it contains only numbers
        and has a minimum length requirement. Raises a ValidationError if the
        phone number contains any non-digit characters or if its length is less
        than 10 characters.
        """
        if not value.isdigit() or len(value) < 10:
            raise serializers.ValidationError(
                "Phone number must be at least 10 digits long and contain only numbers."
            )
        return value
