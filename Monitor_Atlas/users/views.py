from .serializers import (
    UserSerializer,
    CustomTokenObtainPairSerializer,
    CustomTokenRefreshSerializer,
)
from .models import User
from roles.permissions import HasPermission

from rest_framework.viewsets import ModelViewSet
from guardian.shortcuts import get_objects_for_user
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from datetime import timedelta

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken

from drf_spectacular.utils import extend_schema_view, extend_schema
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample

from google.oauth2 import id_token
from google.auth.transport import requests

from .emails import (
    send_verification_email,
    send_password_reset_email,
)
from .jwt import generate_token, verify_token

from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from loguru import logger

from roles.helpers import (
    assign_new_user_base_permissions,
    assign_created_instance_permissions,
)

from support.serializers import SupportMembershipSerializer

# User ViewSet


@extend_schema_view(
    list=extend_schema(description="User List"),
    create=extend_schema(
        description="User Create",
        examples=[
            OpenApiExample(
                "User Create",
                description="Create a new user",
                value={
                    "username": "johndoe",
                    "email": "johndoe@example.com",
                    "code": "string",
                    "name": "John",
                    "last_name": "Doe",
                    "country": "USA",
                    "phone_code": "+1",
                    "phone": "1234567890",
                    "address": {
                        "street": "123 Main St",
                        "city": "Anytown",
                        "state": "CA",
                        "zip_code": "12345",
                    },
                },
                request_only=True,
                response_only=False,
            )
        ],
    ),
    retrieve=extend_schema(description="User Retrieve"),
    update=extend_schema(description="User Update"),
    partial_update=extend_schema(description="User Partial Update"),
    destroy=extend_schema(description="User Destroy"),
    set_user_image=extend_schema(
        description="Set user image",
        summary="Set or update the user's profile image",
        examples=[
            OpenApiExample(
                "Set User Image Example",
                description="Set or update the user's profile image",
                value={"img": "https://example.com/path/to/image.jpg"},
            ),
        ],
    ),
    disable_user=extend_schema(
        description="Disable a user",
        request=OpenApiTypes.NONE,
        examples=[
            OpenApiExample(
                "Disable User Example",
                description="Disable a user account",
                value={"detail": "User disabled successfully."},
                response_only=True,
            ),
        ],
    ),
    enable_user=extend_schema(
        description="Enable a user",
        request=OpenApiTypes.NONE,
        examples=[
            OpenApiExample(
                "Enable User Example",
                description="Enable a user account",
                value={"detail": "User enabled successfully."},
                response_only=True,
            ),
        ],
    ),
    get_support_membership=extend_schema(
        description="Get support membership for a user",
        request=OpenApiTypes.NONE,
        examples=[
            OpenApiExample(
                "Get Support Membership Example",
                description="Get support membership details for a user",
                value={"id": 1},
                response_only=True,
            ),
        ],
    ),
)
class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [HasPermission]
    scope = "user"

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return User.objects.all()
        return get_objects_for_user(
            user,
            "users.view_user",
            klass=User,
            accept_global_perms=False,
        )

    def perform_create(self, serializer):
        user = self.request.user
        instance = serializer.save()
        assign_created_instance_permissions(instance, user)

        if not user.is_superuser:
            tenant = user.tenant
            instance.tenant = tenant
            assign_new_user_base_permissions(instance)
        else:
            instance.tenant = None
            logger.debug("Please, manually add the tenant for this user")

        assign_created_instance_permissions(instance, user)

        token = generate_token(instance.id, scope="set_password", expires_minutes=60)

        send_password_reset_email(instance, token)

        logger.debug(f"Sent password reset email to new user {instance.username}")

    @action(
        detail=True, methods=["patch"], permission_classes=[HasPermission], scope="user"
    )
    def set_user_image(self, request, pk=None):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(
        detail=True, methods=["patch"], permission_classes=[HasPermission], scope="user"
    )
    def disable_user(self, request, pk=None):
        instance = self.get_object()
        instance.is_active = False
        instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(
        detail=True, methods=["patch"], permission_classes=[HasPermission], scope="user"
    )
    def enable_user(self, request, pk=None):
        instance = self.get_object()
        instance.is_active = True
        instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=["get"],
        permission_classes=[HasPermission],
        scope="support_membership",
    )
    def get_support_membership(self, request, pk=None):
        user = self.get_object()
        try:
            support_membership = SupportMembership.objects.get(user=user)
            serializer = SupportMembershipSerializer(support_membership)
            return Response(serializer.data)
        except SupportMembership.DoesNotExist:
            return Response(
                {"error": "This user does not have a support membership."}, status=404
            )


# Authentication
REFRESH_COOKIE_NAME = settings.REFRESH_COOKIE_NAME
REFRESH_COOKIE_PATH = settings.REFRESH_COOKIE_PATH


class CookieTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    @method_decorator(csrf_protect)
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        refresh = response.data.get("refresh")

        response.data.pop("refresh", None)

        refresh_lifetime = settings.SIMPLE_JWT.get("REFRESH_TOKEN_LIFETIME")
        if not isinstance(refresh_lifetime, timedelta):
            refresh_lifetime = timedelta(days=1)
        max_age = int(refresh_lifetime.total_seconds())

        response.set_cookie(
            key=REFRESH_COOKIE_NAME,
            value=refresh,
            max_age=max_age,
            httponly=True,
            secure=settings.COOKIE_SECURE,
            samesite="Lax",
            path=REFRESH_COOKIE_PATH,
        )
        return response


class CookieTokenRefreshView(TokenRefreshView):
    serializer_class = CustomTokenRefreshSerializer

    @method_decorator(csrf_protect)
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get(REFRESH_COOKIE_NAME)

        if not refresh_token:
            return Response(
                {"detail": "Refresh token not found."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        serializer = self.get_serializer(data={"refresh": refresh_token})
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        response = Response(data, status=status.HTTP_200_OK)

        new_refresh = response.data.get("refresh")

        if new_refresh:
            max_age = int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds())
            response.set_cookie(
                key=REFRESH_COOKIE_NAME,
                value=new_refresh,
                max_age=max_age,
                httponly=True,
                secure=getattr(settings, "COOKIE_SECURE", False),
                samesite="Lax",
                path=REFRESH_COOKIE_PATH,
            )

        return response


class LogoutView(APIView):
    @method_decorator(csrf_protect)
    def post(self, request):
        refresh = request.COOKIES.get(REFRESH_COOKIE_NAME)
        if refresh:
            try:
                token = RefreshToken(refresh)
                token.blacklist()
            except Exception as e:
                return Response(
                    {"detail": "Invalid or expired token."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        response = Response(status=status.HTTP_204_NO_CONTENT)
        response.delete_cookie(
            key=REFRESH_COOKIE_NAME, path=REFRESH_COOKIE_PATH, samesite="Lax"
        )
        return response


class GoogleLoginView(APIView):
    permission_classes = [AllowAny]

    @method_decorator(csrf_protect)
    @extend_schema(
        description="Google OAuth2 Login",
        request={
            "application/json": {
                "type": "object",
                "properties": {"id_token": {"type": "string"}},
                "required": ["id_token"],
            }
        },
        examples=[
            OpenApiExample(
                "Google OAuth2 Login Example",
                value={"id_token": "string"},
                request_only=True,
            )
        ],
    )
    def post(self, request):
        token = request.data.get("id_token")
        if not token:
            return Response(
                {"detail": "ID token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            idinfo = id_token.verify_oauth2_token(token, requests.Request())
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_401_UNAUTHORIZED)

        if idinfo["aud"] != settings.GOOGLE_CLIENT_ID:
            return Response(
                {"detail": "Invalid audience."}, status=status.HTTP_401_UNAUTHORIZED
            )
        if idinfo.get("iss") not in [settings.GOOGLE_ISS, "accounts.google.com"]:
            return Response(
                {"detail": "Invalid issuer."}, status=status.HTTP_401_UNAUTHORIZED
            )

        email = idinfo.get("email")
        base_username = email.split("@")[0]
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}_{counter}"
            counter += 1

        sub = idinfo.get("sub")

        if not email or not sub:
            return Response(
                {"detail": "Invalid token payload."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "sub": sub,
                "name": idinfo.get("given_name", ""),
                "last_name": idinfo.get("family_name", ""),
                "is_active": True,
            },
        )

        if created:
            assign_new_user_base_permissions(user)

        refresh = RefreshToken.for_user(user)
        access = str(refresh.access_token)

        refresh_lifetime = settings.SIMPLE_JWT.get("REFRESH_TOKEN_LIFETIME")
        if not isinstance(refresh_lifetime, timedelta):
            refresh_lifetime = timedelta(days=1)
        max_age = int(refresh_lifetime.total_seconds())

        response = Response({"access": access}, status=status.HTTP_200_OK)

        response.set_cookie(
            key=REFRESH_COOKIE_NAME,
            value=refresh,
            max_age=max_age,
            httponly=True,
            secure=settings.COOKIE_SECURE,
            samesite="Lax",
            path=REFRESH_COOKIE_PATH,
        )
        return response


class RegisterView(APIView):
    permission_classes = [AllowAny]

    @method_decorator(csrf_protect)
    @extend_schema(
        description="User Registration",
        request=UserSerializer,
        examples=[
            OpenApiExample(
                "User Registration Example",
                value={
                    "username": "johndoe",
                    "email": "johndoe@example.com",
                    "password": "string",
                    "confirm_password": "string",
                    "name": "John",
                    "last_name": "Doe",
                    "country": "USA",
                    "phone_code": "+1",
                    "phone": "1234567890",
                    "address": {
                        "address": "Cll. 123 #45-67",
                        "city": "Anytown",
                        "state": "CA",
                        "zip_code": "12345",
                    },
                },
                request_only=True,
            )
        ],
    )
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            if not request.data.get("password"):
                return Response({"detail": "Password is required."}, status=400)

            user = serializer.save(is_active=False)

            token = generate_token(user.id, scope="verify_email", expires_minutes=60)

            send_verification_email(user, token)

            return Response(
                {"detail": "User registered successfully. Please verify your email."},
                status=201,
            )
        return Response(serializer.errors, status=400)


class PasswordResetView(APIView):
    permission_classes = [AllowAny]

    @method_decorator(csrf_protect)
    @extend_schema(
        description="Password Reset Request",
        request={
            "application/json": {
                "type": "object",
                "properties": {"email": {"type": "string"}},
                "required": ["email"],
            }
        },
        examples=[
            OpenApiExample(
                "Password Reset Request",
                value={"email": "johndoe@example.com"},
                request_only=True,
            )
        ],
    )
    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"detail": "Email is required."}, status=400)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"detail": "If the email is registered, a reset link has been sent."},
                status=200,
            )

        token = generate_token(user.id, scope="password_reset", expires_minutes=30)

        send_password_reset_email(user, token)

        return Response(
            {"detail": "If the email is registered, a reset link has been sent."},
            status=200,
        )


class AccountVerificationView(APIView):
    permission_classes = [AllowAny]

    @method_decorator(csrf_protect)
    @extend_schema(
        description="Account Verification",
        request={
            "application/json": {
                "type": "object",
                "properties": {"token": {"type": "string"}},
                "required": ["token"],
            }
        },
        examples=[
            OpenApiExample(
                "Account Verification",
                value={"token": "string"},
                request_only=True,
            )
        ],
    )
    def post(self, request):
        token = request.data.get("token")
        if not token:
            return Response({"detail": "Token is required."}, status=400)

        try:
            payload = verify_token(token, expected_scope="verify_email")
            user_id = payload.get("user_id")
            user = User.objects.get(id=user_id)
            user.is_active = True
            user.save()

            assign_new_user_base_permissions(user)

            return Response({"detail": "Account verified successfully."}, status=200)
        except (ValueError, User.DoesNotExist) as e:
            return Response({"detail": str(e)}, status=400)


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    @method_decorator(csrf_protect)
    @extend_schema(
        description="Password Reset Confirmation",
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "token": {"type": "string"},
                    "new_password": {"type": "string"},
                },
                "required": ["token", "new_password"],
            }
        },
        examples=[
            OpenApiExample(
                "Password Reset Confirmation",
                value={"token": "string", "new_password": "SecurePassword123!"},
                request_only=True,
            )
        ],
    )
    def post(self, request):
        token = request.data.get("token")
        new_password = request.data.get("new_password")
        if not token or not new_password:
            return Response(
                {"detail": "Token and new password are required."}, status=400
            )
        try:
            try:
                validate_password(new_password)
            except ValidationError as ve:
                return Response({"detail": ve.messages}, status=400)

            payload = verify_token(
                token, expected_scope=["password_reset", "set_password"]
            )
            user_id = payload.get("user_id")
            user = User.objects.get(id=user_id)
            user.set_password(new_password)
            user.is_active = True
            user.save()
            return Response({"detail": "Password reset successfully."}, status=200)
        except (ValueError, User.DoesNotExist) as e:
            return Response({"detail": str(e)}, status=400)


class ResendVerificationThrottle(AnonRateThrottle):
    """
    Throttle for resend verification email endpoint.
    Limits to 3 requests per hour to prevent abuse.
    """

    rate = "3/hour"


class ReSendVerificationEmailView(APIView):
    """
    Re-send verification email endpoint.

    This endpoint allows users to request a new verification email if:
    - Their account exists but is not active
    - The previous verification token expired

    It accepts an email address and sends a new verification token.
    No authentication required to avoid chicken-egg problem.
    """

    permission_classes = [AllowAny]
    throttle_classes = [ResendVerificationThrottle]

    @method_decorator(csrf_protect)
    @extend_schema(
        description="Re-send account verification email",
        request={
            "application/json": {
                "type": "object",
                "properties": {"email": {"type": "string"}},
                "required": ["email"],
            }
        },
        examples=[
            OpenApiExample(
                "Resend Verification Email",
                value={"email": "johndoe@example.com"},
                request_only=True,
            )
        ],
    )
    def post(self, request):
        email = request.data.get("email")

        if not email:
            return Response(
                {"detail": "Email is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email__iexact=email)

            # If user is already active, don't send email but respond generically
            if user.is_active:
                # Don't leak information that account exists and is active
                return Response(
                    {
                        "detail": "If the account exists and is not verified, a verification email has been sent."
                    },
                    status=status.HTTP_200_OK,
                )

            # User exists and is not active - send verification email
            token = generate_token(user.id, scope="verify_email", expires_minutes=60)
            send_verification_email(user, token)

        except User.DoesNotExist:
            # Don't leak information about whether the email exists
            pass

        # Always return the same response to avoid email enumeration
        return Response(
            {
                "detail": "If the account exists and is not verified, a verification email has been sent."
            },
            status=status.HTTP_200_OK,
        )


class VerifyTicketToken(APIView):
    permission_classes = [AllowAny]

    @method_decorator(csrf_protect)
    @extend_schema(
        description="Verify ticket access token",
        request={
            "application/json": {
                "type": "object",
                "properties": {"token": {"type": "string"}},
                "required": ["token"],
            }
        },
        examples=[
            OpenApiExample(
                "Verify Ticket Token",
                value={"token": "string"},
                request_only=True,
            )
        ],
    )
    def post(self, request):
        token = request.data.get("token")
        if not token:
            return Response({"detail": "Token is required."}, status=400)

        try:
            payload = verify_token(token, expected_scope="ticket_access")
            ticket_id = payload.get("ticket_id")
            return Response({"ticket_id": ticket_id}, status=200)
        except ValueError as e:
            return Response({"detail": str(e)}, status=400)


@ensure_csrf_cookie
@api_view(["GET"])
@permission_classes([AllowAny])
def csrf_setup(request):
    return Response({"detail": "CSRF cookie set."}, status=status.HTTP_200_OK)
