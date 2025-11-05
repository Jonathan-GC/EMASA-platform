from loguru import logger
from rest_framework import serializers
from django.core.validators import validate_email
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from roles.models import WorkspaceMembership
from .models import User, MainAddress, BillingAddress
from support.models import SupportMembership


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
            if user.tenant:
                tenant = user.tenant
                cs_tenant_id = getattr(tenant, "cs_tenant_id", None)
                if cs_tenant_id is None:
                    logger.warning(
                        f"Tenant {tenant.id} for user {user.id} has no ChirpStack tenant ID."
                    )
                    cs_tenant_id = tenant.id
                if tenant.name == "EMASA" or user.is_superuser:
                    is_global = True
                else:
                    is_global = False
            else:
                logger.warning(
                    f"User {user.id} has no tenant or workspace membership; setting is_global to False."
                )
                is_global = False
                cs_tenant_id = None

        support_membership = SupportMembership.objects.filter(user=user).first()
        if support_membership:
            is_support = True
        else:
            is_support = False

        token["user_id"] = user.id
        token["username"] = user.username
        token["is_global"] = is_global
        token["cs_tenant_id"] = cs_tenant_id
        token["is_superuser"] = is_superuser
        token["is_support"] = is_support

        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user

        # Check if the user account is active
        if not user.is_active:
            from rest_framework import exceptions

            # Include the email in the error so frontend can use it for resend
            raise exceptions.AuthenticationFailed(
                {
                    "detail": "Account is not active. Please verify your email.",
                    "code": "account_not_active",
                    "email": user.email,  # Frontend needs this for resend
                }
            )

        return data


class MainAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = MainAddress
        fields = [
            "id",
            "address",
            "city",
            "state",
            "zip_code",
        ]


class BillingAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = BillingAddress
        fields = [
            "id",
            "address",
            "city",
            "state",
            "zip_code",
            "country",
        ]


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    address = MainAddressSerializer(required=False, allow_null=True)
    confirm_password = serializers.CharField(
        write_only=True, required=False, allow_blank=True
    )

    class Meta:
        model = User
        fields = [
            "id",
            "code",
            "username",
            "email",
            "password",
            "confirm_password",
            "img",
            "name",
            "tenant",
            "last_name",
            "is_active",
            "phone",
            "phone_code",
            "address",
        ]

    def validate_password(self, value):
        """
        Validates the password field to ensure that it meets the required
        complexity and strength criteria. Raises a ValidationError if the
        password does not comply with the defined password validators.

        Default validation standards:
        - Minimum length of 8 characters
        - Cannot be entirely numeric
        - Cannot be too common
        - Cannot be too similar to the user's personal information
        """
        if value:
            try:
                validate_password(value)
            except DjangoValidationError as e:
                raise serializers.ValidationError(e.messages)
        return value

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

    def create(self, validated_data):
        address_data = validated_data.pop("address", None)
        password = validated_data.pop("password", None)
        confirm_password = validated_data.pop("confirm_password", None)

        if password and password != confirm_password:
            raise serializers.ValidationError({"password": "Passwords do not match."})

        user = User(**validated_data)

        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save()

        if address_data:
            # MainAddress has no 'user' field — create address and assign to user.address
            address = MainAddress.objects.create(**address_data)
            user.address = address
            user.save()

        return user

    def update(self, instance, validated_data):
        address_data = validated_data.pop("address", None)
        password = validated_data.pop("password", None)
        confirm_password = validated_data.pop("confirm_password", None)

        if password and password != confirm_password:
            raise serializers.ValidationError({"password": "Passwords do not match."})

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()

        if address_data:
            if instance.address:
                for attr, value in address_data.items():
                    setattr(instance.address, attr, value)
                instance.address.save()
            else:
                # Create a MainAddress (no 'user' FK) and assign it to the user
                address = MainAddress.objects.create(**address_data)
                instance.address = address
                instance.save()

        return instance

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Use the User.address FK (not .main_address)
        if instance.address:
            representation["address"] = MainAddressSerializer(instance.address).data
        else:
            representation["address"] = None

        return representation
