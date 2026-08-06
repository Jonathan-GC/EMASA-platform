from loguru import logger
from rest_framework import serializers
from django.core.validators import validate_email
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
)
from roles.models import WorkspaceMembership
from .models import User, MainAddress, BillingAddress
from support.models import SupportMembership
from organizations.models import Tenant
from drf_spectacular.utils import extend_schema_field, inline_serializer
from drf_spectacular.types import OpenApiTypes


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
        is_tenant_admin = False

        if membership:
            if membership.role and membership.role.is_admin:
                is_tenant_admin = True
            tenant = Tenant.objects.get(id=membership.workspace.tenant.id)
            cs_tenant_id = getattr(tenant, "cs_tenant_id", None)
            if tenant.is_global:
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
                if tenant.is_global or user.is_superuser:
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
        token["is_tenant_admin"] = is_tenant_admin

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


class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    """
    Custom Token Refresh Serializer that ensures the new access token
    includes all custom claims (cs_tenant_id, is_global, etc.)
    """

    def validate(self, attrs):
        refresh = self.token_class(attrs["refresh"])
        user_id = refresh.get("user_id")

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            from rest_framework.exceptions import AuthenticationFailed

            raise AuthenticationFailed("User not found")

        data = super().validate(attrs)

        from rest_framework_simplejwt.tokens import AccessToken

        access_token = AccessToken(data["access"])

        membership = (
            WorkspaceMembership.objects.filter(user=user)
            .select_related("workspace__tenant")
            .first()
        )
        is_superuser = user.is_superuser
        is_tenant_admin = False

        if membership:
            if membership.role and membership.role.is_admin:
                is_tenant_admin = True
            tenant = Tenant.objects.get(id=membership.workspace.tenant.id)
            cs_tenant_id = getattr(tenant, "cs_tenant_id", None)
            if tenant.is_global:
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
                if tenant.is_global or user.is_superuser:
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

        access_token["user_id"] = user.id
        access_token["username"] = user.username
        access_token["is_global"] = is_global
        access_token["cs_tenant_id"] = cs_tenant_id
        access_token["is_superuser"] = is_superuser
        access_token["is_support"] = is_support
        access_token["is_tenant_admin"] = is_tenant_admin

        data["access"] = str(access_token)

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
    tenant_name = serializers.ReadOnlyField(source="tenant.name")

    address_address = serializers.CharField(
        write_only=True, required=False, allow_blank=True
    )
    address_city = serializers.CharField(
        write_only=True, required=False, allow_blank=True
    )
    address_state = serializers.CharField(
        write_only=True, required=False, allow_blank=True
    )
    address_zip_code = serializers.CharField(
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
            "tenant_name",
            "last_name",
            "is_active",
            "phone",
            "phone_code",
            "address",
            "address_address",
            "address_city",
            "address_state",
            "address_zip_code",
            "country",
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
        # Extraer campos de dirección aplanados
        address_data = validated_data.pop("address", None)
        address_address = validated_data.pop("address_address", None)
        address_city = validated_data.pop("address_city", None)
        address_state = validated_data.pop("address_state", None)
        address_zip_code = validated_data.pop("address_zip_code", None)

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

        # Si se enviaron campos aplanados de dirección, construir address_data
        if not address_data and any(
            [address_address, address_city, address_state, address_zip_code]
        ):
            address_data = {}
            if address_address:
                address_data["address"] = address_address
            if address_city:
                address_data["city"] = address_city
            if address_state:
                address_data["state"] = address_state
            if address_zip_code:
                address_data["zip_code"] = address_zip_code

        if address_data:
            # MainAddress has no 'user' field — create address and assign to user.address
            address = MainAddress.objects.create(**address_data)
            user.address = address
            user.save()

        return user

    def update(self, instance, validated_data):
        # Extraer campos de dirección aplanados
        address_data = validated_data.pop("address", None)
        address_address = validated_data.pop("address_address", None)
        address_city = validated_data.pop("address_city", None)
        address_state = validated_data.pop("address_state", None)
        address_zip_code = validated_data.pop("address_zip_code", None)

        password = validated_data.pop("password", None)
        confirm_password = validated_data.pop("confirm_password", None)

        if password and password != confirm_password:
            raise serializers.ValidationError({"password": "Passwords do not match."})

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()

        # Si se enviaron campos aplanados de dirección, construir address_data
        if not address_data and any(
            [address_address, address_city, address_state, address_zip_code]
        ):
            address_data = {}
            if address_address:
                address_data["address"] = address_address
            if address_city:
                address_data["city"] = address_city
            if address_state:
                address_data["state"] = address_state
            if address_zip_code:
                address_data["zip_code"] = address_zip_code

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


def _safe_get_url(file_field):
    if not file_field:
        return None
    try:
        return file_field.url
    except Exception:
        return str(file_field) if file_field else None


class UserMeSerializer(UserSerializer):
    tenant = serializers.SerializerMethodField(read_only=True)
    google_oauth = serializers.SerializerMethodField(read_only=True)
    roles = serializers.SerializerMethodField(read_only=True)

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ["google_oauth", "roles"]

    @extend_schema_field(
        inline_serializer(
            name="UserMeTenant",
            fields={
                "id": serializers.CharField(allow_null=True),
                "name": serializers.CharField(),
                "description": serializers.CharField(allow_null=True),
                "img": serializers.CharField(allow_null=True),
            },
        )
    )
    def get_tenant(self, obj):
        tenant = obj.tenant
        if tenant:
            return {
                "id": tenant.id,
                "name": tenant.name,
                "description": tenant.description,
                "img": _safe_get_url(tenant.img),
            }
        return None

    @extend_schema_field(
        inline_serializer(
            name="UserMeGoogleOAuth",
            fields={
                "is_linked": serializers.BooleanField(),
                "email": serializers.CharField(allow_null=True),
                "provider_user_id": serializers.CharField(allow_null=True),
                "created_at": serializers.DateTimeField(allow_null=True),
            },
        )
    )
    def get_google_oauth(self, obj):
        oauth = obj.oauth_accounts.filter(provider="google").first()
        if oauth:
            return {
                "is_linked": True,
                "email": oauth.email,
                "provider_user_id": oauth.provider_user_id,
                "created_at": oauth.created_at,
            }
        return {
            "is_linked": False,
            "email": None,
            "provider_user_id": None,
            "created_at": None,
        }

    @extend_schema_field(
        inline_serializer(
            name="UserMeRole",
            many=True,
            fields={
                "id": serializers.CharField(),
                "name": serializers.CharField(),
                "description": serializers.CharField(allow_null=True),
                "color": serializers.CharField(allow_null=True),
                "is_admin": serializers.BooleanField(),
                "workspace": inline_serializer(
                    name="UserMeRoleWorkspace",
                    fields={
                        "id": serializers.CharField(),
                        "name": serializers.CharField(),
                    },
                    allow_null=True,
                ),
            },
        )
    )
    def get_roles(self, obj):
        from roles.models import WorkspaceMembership

        memberships = WorkspaceMembership.objects.filter(user=obj).select_related(
            "role", "workspace"
        )
        roles_list = []
        for membership in memberships:
            roles_list.append(
                {
                    "id": membership.role.id,
                    "name": membership.role.name,
                    "description": membership.role.description,
                    "color": membership.role.color,
                    "is_admin": membership.role.is_admin,
                    "workspace": (
                        {
                            "id": membership.workspace.id,
                            "name": membership.workspace.name,
                        }
                        if membership.workspace
                        else None
                    ),
                }
            )
        return roles_list


class UserProfileSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField(read_only=True)
    user_info = serializers.SerializerMethodField(read_only=True)
    status = serializers.SerializerMethodField(read_only=True)
    tenant = serializers.SerializerMethodField(read_only=True)
    contact_info = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = [
            "roles",
            "user_info",
            "status",
            "tenant",
            "contact_info",
        ]

    @extend_schema_field(
        inline_serializer(
            name="UserProfileRole",
            many=True,
            fields={
                "id": serializers.CharField(),
                "name": serializers.CharField(),
                "description": serializers.CharField(allow_null=True),
                "color": serializers.CharField(allow_null=True),
                "is_admin": serializers.BooleanField(),
                "workspace": inline_serializer(
                    name="UserProfileRoleWorkspace",
                    fields={
                        "id": serializers.CharField(),
                        "name": serializers.CharField(),
                    },
                    allow_null=True,
                ),
            },
        )
    )
    def get_roles(self, obj):
        from roles.models import WorkspaceMembership

        memberships = WorkspaceMembership.objects.filter(user=obj).select_related(
            "role", "workspace"
        )
        roles_list = []
        for membership in memberships:
            roles_list.append(
                {
                    "id": membership.role.id,
                    "name": membership.role.name,
                    "description": membership.role.description,
                    "color": membership.role.color,
                    "is_admin": membership.role.is_admin,
                    "workspace": (
                        {
                            "id": membership.workspace.id,
                            "name": membership.workspace.name,
                        }
                        if membership.workspace
                        else None
                    ),
                }
            )
        return roles_list

    @extend_schema_field(
        inline_serializer(
            name="UserProfileUserInfo",
            fields={
                "id": serializers.CharField(),
                "code": serializers.CharField(allow_null=True),
                "username": serializers.CharField(),
                "email": serializers.CharField(),
                "name": serializers.CharField(),
                "last_name": serializers.CharField(),
                "full_name": serializers.CharField(),
                "img": serializers.CharField(allow_null=True),
                "is_staff": serializers.BooleanField(),
                "is_superuser": serializers.BooleanField(),
            },
        )
    )
    def get_user_info(self, obj):
        return {
            "id": obj.id,
            "code": obj.code,
            "username": obj.username,
            "email": obj.email,
            "name": obj.name,
            "last_name": obj.last_name,
            "full_name": obj.get_full_name(),
            "img": _safe_get_url(obj.img),
            "is_staff": obj.is_staff,
            "is_superuser": obj.is_superuser,
        }

    @extend_schema_field(
        inline_serializer(
            name="UserProfileStatus",
            fields={
                "is_active": serializers.BooleanField(),
                "status_text": serializers.CharField(),
            },
        )
    )
    def get_status(self, obj):
        return {
            "is_active": obj.is_active,
            "status_text": "Active" if obj.is_active else "Inactive",
        }

    @extend_schema_field(
        inline_serializer(
            name="UserProfileTenant",
            fields={
                "id": serializers.CharField(allow_null=True),
                "name": serializers.CharField(),
                "description": serializers.CharField(allow_null=True),
                "img": serializers.CharField(allow_null=True),
            },
        )
    )
    def get_tenant(self, obj):
        tenant = obj.tenant
        if tenant:
            return {
                "id": tenant.id,
                "name": tenant.name,
                "description": tenant.description,
                "img": _safe_get_url(tenant.img),
            }
        return None

    @extend_schema_field(
        inline_serializer(
            name="UserProfileContactInfo",
            fields={
                "email": serializers.CharField(),
                "phone": serializers.CharField(allow_null=True),
                "phone_code": serializers.CharField(allow_null=True),
                "country": serializers.CharField(allow_null=True),
                "address": MainAddressSerializer(allow_null=True),
                "billing_address": BillingAddressSerializer(allow_null=True),
            },
        )
    )
    def get_contact_info(self, obj):
        contact = {
            "email": obj.email,
            "phone": obj.phone,
            "phone_code": obj.phone_code,
            "country": obj.country,
            "address": MainAddressSerializer(obj.address).data if obj.address else None,
        }
        if hasattr(obj, "billing_address") and obj.billing_address:
            contact["billing_address"] = BillingAddressSerializer(
                obj.billing_address
            ).data
        else:
            contact["billing_address"] = None
        return contact


from auditlog.models import LogEntry


class LogEntrySerializer(serializers.ModelSerializer):
    model = serializers.SerializerMethodField()
    app = serializers.SerializerMethodField()
    action_name = serializers.CharField(source="get_action_display", read_only=True)
    detail = serializers.SerializerMethodField()
    actor_details = serializers.SerializerMethodField()
    formatted_changes = serializers.SerializerMethodField()

    class Meta:
        model = LogEntry
        fields = [
            "id",
            "action",
            "action_name",
            "detail",
            "model",
            "app",
            "content_type",
            "object_pk",
            "object_repr",
            "serialized_data",
            "actor",
            "actor_details",
            "remote_addr",
            "timestamp",
            "changes",
            "formatted_changes",
            "additional_data",
        ]

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_model(self, obj):
        if obj.content_type:
            return obj.content_type.model
        return None

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_app(self, obj):
        if obj.content_type:
            return obj.content_type.app_label
        return None

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_detail(self, obj):
        if obj.additional_data and isinstance(obj.additional_data, dict):
            return obj.additional_data.get("action_detail")
        return None

    @extend_schema_field(serializers.DictField(allow_null=True))
    def get_actor_details(self, obj):
        if not obj.actor:
            return None
        full_name = f"{getattr(obj.actor, 'name', '')} {getattr(obj.actor, 'last_name', '')}".strip()
        return {
            "id": obj.actor.id,
            "username": getattr(obj.actor, "username", ""),
            "email": getattr(obj.actor, "email", ""),
            "full_name": full_name or getattr(obj.actor, "username", "Unknown User"),
        }

    @extend_schema_field(serializers.ListField(child=serializers.CharField()))
    def get_formatted_changes(self, obj):
        changes = obj.changes
        if not changes:
            return []

        if isinstance(changes, str):
            try:
                import json
                changes = json.loads(changes)
            except Exception:
                return [changes]

        if not isinstance(changes, dict):
            return []

        formatted = []
        for field, diff in changes.items():
            if isinstance(diff, list) and len(diff) == 2:
                old_val, new_val = diff[0], diff[1]
                formatted.append(f"Changed '{field}' from '{old_val}' to '{new_val}'")
            else:
                formatted.append(f"Modified '{field}': {diff}")
        return formatted


