from .serializers import (
    UserSerializer,
    UserMeSerializer,
    UserProfileSerializer,
    CustomTokenObtainPairSerializer,
    CustomTokenRefreshSerializer,
    LogEntrySerializer,
    OTPRequestSerializer,
    OTPVerifySerializer,
)
from .models import User, OAuthAccount
from roles.permissions import HasPermission
from auditlog.models import LogEntry
from django.db.models import Q
from platform_backend.audit_mixins import AuditActionMixin

from rest_framework.viewsets import ModelViewSet
from guardian.shortcuts import get_objects_for_user
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect, csrf_exempt, ensure_csrf_cookie
from django.middleware.csrf import CsrfViewMiddleware
from datetime import timedelta
from functools import wraps
import urllib.parse

import requests as http_requests

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status, viewsets, serializers
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken

from drf_spectacular.utils import (
    extend_schema_view,
    extend_schema,
    OpenApiExample,
    OpenApiResponse,
    OpenApiParameter,
    inline_serializer,
)
from drf_spectacular.types import OpenApiTypes

from google.oauth2 import id_token
from google.auth.transport import requests

from .emails import (
    send_verification_email,
    send_password_reset_email,
    send_otp_email,
)
from .jwt import generate_token, verify_token

from django.core.cache import cache
import secrets

from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from loguru import logger

from roles.helpers import (
    assign_new_user_base_permissions,
    assign_created_instance_permissions,
)

from support.serializers import SupportMembershipSerializer

from roles.permissions import IsAnAdminUser, IsTenantAdminUser

# User ViewSet


@extend_schema_view(
    list=extend_schema(
        summary="List users",
        description="Filter users by workspace if 'workspace' query parameter is provided.",
        responses={200: UserSerializer(many=True)},
    ),
    create=extend_schema(
        summary="Create user",
        description="Create a new user account.",
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
        responses={201: UserSerializer, 400: OpenApiResponse(description="Validation error")},
    ),
    retrieve=extend_schema(
        summary="Retrieve user",
        description="Retrieve user by ID.",
        responses={200: UserSerializer, 404: OpenApiResponse(description="User not found")},
    ),
    update=extend_schema(
        summary="Update user",
        description="Update user details.",
        responses={200: UserSerializer, 400: OpenApiResponse(description="Validation error")},
    ),
    partial_update=extend_schema(
        summary="Partial update user",
        description="Partially update user details.",
        responses={200: UserSerializer, 400: OpenApiResponse(description="Validation error")},
    ),
    destroy=extend_schema(
        summary="Delete user",
        description="Delete a user account.",
        responses={204: OpenApiResponse(description="User deleted successfully.")},
    ),
    set_user_image=extend_schema(
        summary="Set or update profile image",
        description="Set or update the user's profile image",
        examples=[
            OpenApiExample(
                "Set User Image Example",
                description="Set or update the user's profile image",
                value={"img": "https://example.com/path/to/image.jpg"},
            ),
        ],
        responses={200: UserSerializer},
    ),
    disable_user=extend_schema(
        summary="Disable user",
        description="Disable a user account (is_active=False)",
        request=OpenApiTypes.NONE,
        examples=[
            OpenApiExample(
                "Disable User Example",
                description="Disable a user account",
                value={"detail": "User disabled successfully."},
                response_only=True,
            ),
        ],
        responses={200: UserSerializer},
    ),
    enable_user=extend_schema(
        summary="Enable user",
        description="Enable a user account (is_active=True)",
        request=OpenApiTypes.NONE,
        examples=[
            OpenApiExample(
                "Enable User Example",
                description="Enable a user account",
                value={"detail": "User enabled successfully."},
                response_only=True,
            ),
        ],
        responses={200: UserSerializer},
    ),
    get_support_membership=extend_schema(
        summary="Get support membership for a user",
        description="Get support membership details for a user",
        request=OpenApiTypes.NONE,
        examples=[
            OpenApiExample(
                "Get Support Membership Example",
                description="Get support membership details for a user",
                value={"id": 1},
                response_only=True,
            ),
        ],
        responses={
            200: SupportMembershipSerializer,
            404: OpenApiResponse(description="This user does not have a support membership."),
        },
    ),
    me=extend_schema(
        summary="Get current user ('me')",
        description="Returns details for the currently authenticated user including Google OAuth status, tenant details, and assigned workspace roles.",
        responses={200: UserMeSerializer},
    ),
    profile=extend_schema(
        summary="Get user profile",
        description="Returns full profile structure for a user including roles, user info, active status, tenant, and contact info.",
        responses={200: UserProfileSerializer},
    ),
)
class UserViewSet(AuditActionMixin, ModelViewSet):
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

    def list(self, request, *args, **kwargs):
        """Filter users by workspace if 'workspace' query param is provided.
        It checks the workspace membership of the users."""
        workspace = request.query_params.get("workspace", None)
        queryset = self.get_queryset()
        if workspace:
            queryset = queryset.filter(
                workspacemembership__workspace__id=workspace
            ).distinct()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

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

    @action(
        detail=False,
        methods=["get"],
        permission_classes=[HasPermission],
        scope="user",
    )
    def me(self, request):
        user = request.user
        serializer = UserMeSerializer(user)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=["get"],
        permission_classes=[HasPermission],
        scope="user",
    )
    def profile(self, request, pk=None):
        user = self.get_object()
        serializer = UserProfileSerializer(user)
        return Response(serializer.data)


# Authentication
REFRESH_COOKIE_NAME = settings.REFRESH_COOKIE_NAME
REFRESH_COOKIE_PATH = settings.REFRESH_COOKIE_PATH

# ============================================================================
# Custom CSRF Protection for Native Apps
# ============================================================================


def conditional_csrf_protect(view_func):
    """
    Decorator that applies CSRF protection only for web browsers.
    Allows requests from native apps without CSRF token.

    Detects native apps by:
    - User-Agent contains "Capacitor" or "Ionic"
    - Origin/Referer contain "capacitor://" or "ionic://"
    - Header X-Requested-With contains "com.example.proofoconcept" (your app ID)
    """

    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        user_agent = request.META.get("HTTP_USER_AGENT", "").lower()
        origin = request.META.get("HTTP_ORIGIN", "").lower()
        referer = request.META.get("HTTP_REFERER", "").lower()
        x_requested_with = request.META.get("HTTP_X_REQUESTED_WITH", "").lower()

        is_native_app = (
            "capacitor" in user_agent
            or "ionic" in user_agent
            or "capacitor://" in origin
            or "ionic://" in origin
            or "capacitor://" in referer
            or "ionic://" in referer
            or "com.example.proofoconcept" in x_requested_with
        )

        if is_native_app:
            logger.info(f"🔓 Native app detected - CSRF exempt | UA: {user_agent[:50]}")

        if is_native_app:
            return view_func(request, *args, **kwargs)

        logger.info("🔒 Web browser detected - CSRF protection applied")
        return csrf_protect(view_func)(request, *args, **kwargs)

    return wrapped_view


class CookieTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    @method_decorator(conditional_csrf_protect)
    @extend_schema(
        tags=["Authentication"],
        summary="Login Step 1: Validate Password & Trigger Mandatory 2FA OTP",
        description=(
            "### Mandatory 2FA Login Flow (Step 1 of 2):\n"
            "1. Client submits `username` and `password`.\n"
            "2. Server validates credentials.\n"
            "3. If credentials are valid, a 6-digit 2FA OTP code is generated, uniquely bound to this username, and emailed to the user's registered address.\n"
            "4. Tokens are **NOT** issued in this step. Client receives `requires_2fa: true` and must submit `{ \"username\": username, \"code\": code }` to `/api/v1/users/auth/otp/verify/` to complete authentication."
        ),
        responses={
            200: OpenApiResponse(
                description="Password verified. 2FA verification code sent to user email.",
                response=inline_serializer(
                    name="TwoFactorRequiredResponse",
                    fields={
                        "requires_2fa": serializers.BooleanField(default=True),
                        "username": serializers.CharField(),
                        "email": serializers.CharField(allow_null=True),
                        "detail": serializers.CharField(),
                    },
                ),
            ),
            401: OpenApiResponse(
                description="Invalid credentials or account inactive.",
                response=OpenApiTypes.OBJECT,
            ),
        },
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)

        user = getattr(serializer, "user", None)
        if not user:
            return Response(
                {"detail": "No active account found with the given credentials"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Generate 6-digit 2FA OTP code
        otp_code = f"{secrets.randbelow(1000000):06d}"
        cache_key = f"otp_data_{user.username.lower()}"
        cache.set(
            cache_key,
            {
                "code": otp_code,
                "attempts": 0,
                "user_id": str(user.id),
                "username": user.username.lower(),
            },
            timeout=300,
        )

        try:
            send_otp_email(user, otp_code)
        except Exception as e:
            logger.error(f"Failed to send 2FA OTP email to {user.email}: {str(e)}")
            return Response(
                {"detail": "Credentials valid, but error sending 2FA verification email. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        logger.info(f"🔐 Mandatory 2FA step 1 complete for user {user.username}. OTP sent to {user.email}")
        return Response(
            {
                "requires_2fa": True,
                "username": user.username,
                "email": user.email,
                "detail": "Password verified. Enter the 2FA code sent to your email to complete login.",
            },
            status=status.HTTP_200_OK,
        )



class CookieTokenRefreshView(TokenRefreshView):
    serializer_class = CustomTokenRefreshSerializer

    @method_decorator(conditional_csrf_protect)
    @extend_schema(
        summary="Refresh JWT token (Cookie)",
        description="Refreshes access token using the HTTP-only refresh token cookie.",
        responses={
            200: OpenApiResponse(
                description="Token refreshed successfully.",
                response=OpenApiTypes.OBJECT,
            ),
            401: OpenApiResponse(
                description="Refresh token not found or invalid.",
                response=OpenApiTypes.OBJECT,
            ),
        },
    )
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
    @method_decorator(conditional_csrf_protect)
    @extend_schema(
        summary="Logout user",
        description="Blacklists the HTTP-only refresh token cookie and deletes the cookie.",
        request=OpenApiTypes.NONE,
        responses={
            204: OpenApiResponse(description="Logged out successfully."),
            400: OpenApiResponse(description="Invalid or expired token."),
        },
    )
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


def _resolve_redirect_uri(value):
    """
    Validate and return a redirect_uri against the server's allow-list.

    Returns the sanitised URI on success, or ``None`` when *value* is
    empty/``None`` (the caller should fall back to the default).
    Raises ``ValueError`` if *value* is not in the allowed set.
    """
    if not value:
        return None
    allowed = settings.GOOGLE_ALLOWED_REDIRECT_URIS
    if value not in allowed:
        raise ValueError(f"redirect_uri is not allowed: {value!r}")
    return value


class GoogleLoginUrlView(APIView):
    """
    Returns the Google OAuth2 authorization URL for the frontend
    to redirect the user to.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        summary="Google OAuth2 authorization URL",
        description=(
            "Returns the Google OAuth2 consent-page URL that the frontend "
            "should redirect the user to.  The URL includes the required "
            "`client_id`, `redirect_uri`, `response_type=code` and `scope` "
            "parameters.\n\n"
            "An optional **query parameter** ``?redirect_uri=…`` can be "
            "supplied to override the default web callback.  The value must "
            "be listed in ``GOOGLE_ALLOWED_REDIRECT_URIS``."
        ),
        parameters=[
            OpenApiParameter(
                name="redirect_uri",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description=(
                    "Optional override for the OAuth redirect URI. "
                    "Must belong to ``GOOGLE_ALLOWED_REDIRECT_URIS``."
                ),
            )
        ],
        responses={
            200: OpenApiResponse(
                description="Authorization URL ready for redirect.",
                response=OpenApiTypes.OBJECT,
            ),
            400: OpenApiResponse(
                description="The supplied `redirect_uri` is not allowed.",
                response=OpenApiTypes.OBJECT,
            ),
            501: OpenApiResponse(
                description="Google OAuth is not configured on this server.",
                response=OpenApiTypes.OBJECT,
            ),
        },
        examples=[
            OpenApiExample(
                "Success (web fallback)",
                value={
                    "url": "https://accounts.google.com/o/oauth2/v2/auth"
                    "?client_id=xxx&redirect_uri=http://localhost:5173/auth/callback"
                    "&response_type=code&scope=openid+email+profile"
                    "&access_type=offline&prompt=consent"
                },
                response_only=True,
                status_codes=["200"],
            ),
            OpenApiExample(
                "Success (native app)",
                value={
                    "url": "https://accounts.google.com/o/oauth2/v2/auth"
                    "?client_id=xxx&redirect_uri=com.example.app%3A%2Foauth2redirect"
                    "&response_type=code&scope=openid+email+profile"
                    "&access_type=offline&prompt=consent"
                },
                response_only=True,
                status_codes=["200"],
            ),
            OpenApiExample(
                "Invalid redirect_uri",
                value={"detail": "redirect_uri is not allowed: ..."},
                response_only=True,
                status_codes=["400"],
            ),
            OpenApiExample(
                "Not configured",
                value={"detail": "Google OAuth is not configured."},
                response_only=True,
                status_codes=["501"],
            ),
        ],
    )
    def get(self, request):
        if not settings.GOOGLE_CLIENT_ID:
            return Response(
                {"detail": "Google OAuth is not configured."},
                status=status.HTTP_501_NOT_IMPLEMENTED,
            )

        raw_uri = request.query_params.get("redirect_uri")
        try:
            resolved = _resolve_redirect_uri(raw_uri)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        redirect_uri = (
            resolved if resolved is not None else settings.GOOGLE_REDIRECT_URI
        )

        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": settings.GOOGLE_SCOPE,
            "access_type": "offline",
            "prompt": "consent",
        }
        url = f"{settings.GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}"
        return Response({"url": url})


class GoogleCallbackView(APIView):
    """
    Handles the Google OAuth2 callback.
    Exchanges the authorization code for tokens, then logs the user in
    only if a matching OAuthAccount exists.
    """

    permission_classes = [AllowAny]

    @method_decorator(csrf_protect)
    @extend_schema(
        summary="Google OAuth2 callback",
        description=(
            "Exchanges the authorization `code` the frontend received from "
            "Google for an ID token, validates it, and logs the user in "
            "**only if** a matching `OAuthAccount` exists.\n\n"
            "Google authentication does **not** create new accounts — users "
            "must register with email and password first, then link their "
            "Google identity via `auth/google/link/`.  If no linked account "
            "is found a **404 Not Found** is returned with the Google email "
            "so the frontend can pre-fill the registration form."
        ),
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "code": {"type": "string"},
                    "redirect_uri": {
                        "type": "string",
                        "description": (
                            "Optional.  The redirect URI that was used to "
                            "obtain the authorization code.  Must belong to "
                            "``GOOGLE_ALLOWED_REDIRECT_URIS``.  Defaults to "
                            "the web ``GOOGLE_REDIRECT_URI`` if omitted."
                        ),
                    },
                },
                "required": ["code"],
            }
        },
        responses={
            200: OpenApiResponse(
                description=(
                    "Authentication successful.  Returns a short-lived JWT "
                    "`access` token in the response body and sets a long-lived "
                    "refresh token in an HTTP-only cookie."
                ),
                response=OpenApiTypes.OBJECT,
            ),
            400: OpenApiResponse(
                description=(
                    "Missing `code`, invalid payload, unsupported "
                    "`redirect_uri`, or token exchange failure."
                ),
                response=OpenApiTypes.OBJECT,
            ),
            401: OpenApiResponse(
                description="Invalid ID token, audience, or issuer.",
                response=OpenApiTypes.OBJECT,
            ),
            404: OpenApiResponse(
                description=(
                    "No `OAuthAccount` is linked to this Google identity.  "
                    "The user must register first and then link their account."
                ),
                response=OpenApiTypes.OBJECT,
            ),
        },
        examples=[
            OpenApiExample(
                "Request body — web",
                value={"code": "4/0AanRRr..."},
                request_only=True,
            ),
            OpenApiExample(
                "Request body — native app",
                value={"code": "4/0AanRRr...", "redirect_uri": ""},
                request_only=True,
            ),
            OpenApiExample(
                "Success — tokens issued",
                value={"access": "eyJhbGciOiJIUzI1NiIs..."},
                response_only=True,
                status_codes=["200"],
            ),
            OpenApiExample(
                "Missing code",
                value={"detail": "Authorization code is required."},
                response_only=True,
                status_codes=["400"],
            ),
            OpenApiExample(
                "Invalid ID token",
                value={"detail": "Invalid token."},
                response_only=True,
                status_codes=["401"],
            ),
            OpenApiExample(
                "No linked account",
                value={
                    "detail": (
                        "No account is linked to this Google identity. "
                        "Please register with email and password first, "
                        "then link your Google account in settings."
                    ),
                    "code": "no_linked_account",
                    "email": "user@example.com",
                },
                response_only=True,
                status_codes=["404"],
            ),
        ],
    )
    def post(self, request):
        code = request.data.get("code")
        if not code:
            return Response(
                {"detail": "Authorization code is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        raw_uri = request.data.get("redirect_uri")
        try:
            resolved = _resolve_redirect_uri(raw_uri)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        redirect_uri = (
            resolved if resolved is not None else settings.GOOGLE_REDIRECT_URI
        )

        idinfo = self._exchange_and_verify(code, redirect_uri)
        if isinstance(idinfo, Response):
            return idinfo

        sub = idinfo.get("sub")

        if not sub:
            return Response(
                {"detail": "Invalid token payload."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            oauth_account = OAuthAccount.objects.get(
                provider="google", provider_user_id=sub
            )
            user = oauth_account.user
        except OAuthAccount.DoesNotExist:
            return Response(
                {
                    "detail": (
                        "No account is linked to this Google identity. "
                        "Please register with email and password first, "
                        "then link your Google account in settings."
                    ),
                    "code": "no_linked_account",
                    "email": idinfo.get("email"),
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if not user.is_active:
            user.is_active = True
            user.save()

        return self._issue_tokens(user)

    def _exchange_and_verify(self, code, redirect_uri):
        token_data = {
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_SECRET,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }

        try:
            token_response = http_requests.post(
                settings.GOOGLE_TOKEN_URL,
                data=token_data,
                timeout=10,
            )
            token_response.raise_for_status()
            token_json = token_response.json()
        except Exception as e:
            logger.error(f"Google token exchange failed: {e}")
            return Response(
                {"detail": "Failed to exchange authorization code."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        google_id_token = token_json.get("id_token")
        if not google_id_token:
            return Response(
                {"detail": "No ID token received from Google."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            idinfo = id_token.verify_oauth2_token(google_id_token, requests.Request())
        except ValueError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if idinfo["aud"] != settings.GOOGLE_CLIENT_ID:
            return Response(
                {"detail": "Invalid audience."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if idinfo.get("iss") not in [settings.GOOGLE_ISS, "accounts.google.com"]:
            return Response(
                {"detail": "Invalid issuer."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        return idinfo

    def _issue_tokens(self, user):
        refresh = CustomTokenObtainPairSerializer.get_token(user)
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


class GoogleLinkView(APIView):
    """
    Allows an authenticated user to link their Google account.
    Accepts an authorization code, verifies it, and creates an
    OAuthAccount tied to the current user.
    """

    permission_classes = [IsAuthenticated]

    @method_decorator(csrf_protect)
    @extend_schema(
        summary="Link a Google account",
        description=(
            "Exchanges a Google authorization `code` for an ID token, "
            "validates it, and attaches a new `OAuthAccount` record to the "
            "**currently authenticated user**.\n\n"
            "Use this after the user logs in with their password and wants "
            "to link their Google identity for future OAuth logins.  If the "
            "Google account is already linked to *another* user a **409 "
            "Conflict** is returned."
        ),
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "code": {"type": "string"},
                    "redirect_uri": {
                        "type": "string",
                        "description": (
                            "Optional.  The redirect URI that was used to "
                            "obtain the authorization code.  Must belong to "
                            "``GOOGLE_ALLOWED_REDIRECT_URIS``.  Defaults to "
                            "the web ``GOOGLE_REDIRECT_URI`` if omitted."
                        ),
                    },
                },
                "required": ["code"],
            }
        },
        responses={
            200: OpenApiResponse(
                description="Account linked successfully.",
                response=OpenApiTypes.OBJECT,
            ),
            400: OpenApiResponse(
                description=(
                    "Missing `code`, invalid payload, unsupported "
                    "`redirect_uri`, or token exchange failure."
                ),
                response=OpenApiTypes.OBJECT,
            ),
            401: OpenApiResponse(
                description=(
                    "Invalid ID token, audience, or issuer — or the request "
                    "is not authenticated."
                ),
                response=OpenApiTypes.OBJECT,
            ),
            409: OpenApiResponse(
                description="This Google account is already linked to another user.",
                response=OpenApiTypes.OBJECT,
            ),
        },
        examples=[
            OpenApiExample(
                "Request body — web",
                value={"code": "4/0AanRRr..."},
                request_only=True,
            ),
            OpenApiExample(
                "Request body — native app",
                value={"code": "4/0AanRRr...", "redirect_uri": ""},
                request_only=True,
            ),
            OpenApiExample(
                "Success",
                value={"detail": "Google account linked successfully."},
                response_only=True,
                status_codes=["200"],
            ),
            OpenApiExample(
                "Missing code",
                value={"detail": "Authorization code is required."},
                response_only=True,
                status_codes=["400"],
            ),
            OpenApiExample(
                "Already linked",
                value={
                    "detail": "This Google account is already linked to another user."
                },
                response_only=True,
                status_codes=["409"],
            ),
        ],
    )
    def post(self, request):
        code = request.data.get("code")
        if not code:
            return Response(
                {"detail": "Authorization code is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        raw_uri = request.data.get("redirect_uri")
        try:
            resolved = _resolve_redirect_uri(raw_uri)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        redirect_uri = (
            resolved if resolved is not None else settings.GOOGLE_REDIRECT_URI
        )

        token_data = {
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_SECRET,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }

        try:
            token_response = http_requests.post(
                settings.GOOGLE_TOKEN_URL,
                data=token_data,
                timeout=10,
            )
            token_response.raise_for_status()
            token_json = token_response.json()
        except Exception as e:
            logger.error(f"Google token exchange failed during link: {e}")
            return Response(
                {"detail": "Failed to exchange authorization code."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        google_id_token = token_json.get("id_token")
        if not google_id_token:
            return Response(
                {"detail": "No ID token received from Google."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            idinfo = id_token.verify_oauth2_token(google_id_token, requests.Request())
        except ValueError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if idinfo["aud"] != settings.GOOGLE_CLIENT_ID:
            return Response(
                {"detail": "Invalid audience."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if idinfo.get("iss") not in [settings.GOOGLE_ISS, "accounts.google.com"]:
            return Response(
                {"detail": "Invalid issuer."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        sub = idinfo.get("sub")
        email = idinfo.get("email")

        if not sub or not email:
            return Response(
                {"detail": "Invalid token payload."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if OAuthAccount.objects.filter(
            provider="google", provider_user_id=sub
        ).exists():
            return Response(
                {"detail": "This Google account is already linked to another user."},
                status=status.HTTP_409_CONFLICT,
            )

        OAuthAccount.objects.create(
            user=request.user,
            provider="google",
            provider_user_id=sub,
            email=email,
        )

        return Response({"detail": "Google account linked successfully."})


class GoogleUnlinkView(APIView):
    """
    Allows an authenticated user to unlink their Google account.
    Removes the OAuthAccount record associated with the current user.
    """

    permission_classes = [IsAuthenticated]

    @method_decorator(csrf_protect)
    @extend_schema(
        summary="Unlink a Google account",
        description=(
            "Removes the `OAuthAccount` record associated with the "
            "**currently authenticated user**.\n\n"
            "If no Google account is linked to the current user, returns a "
            "**400 Bad Request**."
        ),
        request=OpenApiTypes.NONE,
        responses={
            200: OpenApiResponse(
                description="Google account unlinked successfully.",
                response=OpenApiTypes.OBJECT,
            ),
            400: OpenApiResponse(
                description="No Google account linked to this user.",
                response=OpenApiTypes.OBJECT,
            ),
            401: OpenApiResponse(
                description="Authentication credentials were not provided.",
                response=OpenApiTypes.OBJECT,
            ),
        },
        examples=[
            OpenApiExample(
                "Success",
                value={"detail": "Google account unlinked successfully."},
                response_only=True,
                status_codes=["200"],
            ),
            OpenApiExample(
                "Not linked",
                value={"detail": "No Google account linked to this user."},
                response_only=True,
                status_codes=["400"],
            ),
        ],
    )
    def post(self, request):
        return self._unlink(request)

    @method_decorator(csrf_protect)
    @extend_schema(
        summary="Unlink a Google account (DELETE)",
        description=(
            "Removes the `OAuthAccount` record associated with the "
            "**currently authenticated user**."
        ),
        request=OpenApiTypes.NONE,
        responses={
            200: OpenApiResponse(
                description="Google account unlinked successfully.",
                response=OpenApiTypes.OBJECT,
            ),
            400: OpenApiResponse(
                description="No Google account linked to this user.",
                response=OpenApiTypes.OBJECT,
            ),
            401: OpenApiResponse(
                description="Authentication credentials were not provided.",
                response=OpenApiTypes.OBJECT,
            ),
        },
    )
    def delete(self, request):
        return self._unlink(request)

    def _unlink(self, request):
        deleted_count, _ = OAuthAccount.objects.filter(
            user=request.user, provider="google"
        ).delete()

        if deleted_count == 0:
            return Response(
                {"detail": "No Google account linked to this user."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"detail": "Google account unlinked successfully."},
            status=status.HTTP_200_OK,
        )


class RegisterView(APIView):
    permission_classes = [AllowAny]

    @method_decorator(csrf_protect)
    @extend_schema(
        summary="User Registration",
        description="Creates a new inactive user account and sends an email verification link.",
        request=UserSerializer,
        responses={
            201: OpenApiResponse(description="User registered successfully. Please verify your email."),
            400: OpenApiResponse(description="Validation error or missing password."),
        },
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
        summary="Password Reset Request",
        description="Sends a password reset email if the specified email address belongs to a registered account.",
        request=inline_serializer(
            name="PasswordResetRequest",
            fields={"email": serializers.EmailField()},
        ),
        responses={
            200: OpenApiResponse(description="If the email is registered, a reset link has been sent."),
            400: OpenApiResponse(description="Email is required."),
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
        summary="Account Verification",
        description="Verifies user email account using a token.",
        request=inline_serializer(
            name="AccountVerificationRequest",
            fields={"token": serializers.CharField()},
        ),
        responses={
            200: OpenApiResponse(description="Account verified successfully."),
            400: OpenApiResponse(description="Token is required or invalid."),
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
        summary="Password Reset Confirmation",
        description="Resets the password for a user using a valid token.",
        request=inline_serializer(
            name="PasswordResetConfirmRequest",
            fields={
                "token": serializers.CharField(),
                "new_password": serializers.CharField(),
            },
        ),
        responses={
            200: OpenApiResponse(description="Password reset successfully."),
            400: OpenApiResponse(description="Token and new password required or invalid."),
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
        summary="Re-send account verification email",
        description="Re-sends account verification email if the account exists and is not verified.",
        request=inline_serializer(
            name="ResendVerificationRequest",
            fields={"email": serializers.EmailField()},
        ),
        responses={
            200: OpenApiResponse(description="If the account exists and is not verified, a verification email has been sent."),
            400: OpenApiResponse(description="Email is required."),
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
        summary="Verify ticket access token",
        description="Verifies a ticket access token and returns ticket_id.",
        request=inline_serializer(
            name="VerifyTicketTokenRequest",
            fields={"token": serializers.CharField()},
        ),
        responses={
            200: OpenApiResponse(description="Token verified successfully. Returns ticket_id."),
            400: OpenApiResponse(description="Token is required or invalid."),
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


@extend_schema(
    summary="Set CSRF cookie",
    description="Ensures that the CSRF cookie is set on the client browser.",
    responses={200: OpenApiResponse(description="CSRF cookie set.")},
)
@ensure_csrf_cookie
@api_view(["GET"])
@permission_classes([AllowAny])
def csrf_setup(request):
    return Response({"detail": "CSRF cookie set."}, status=status.HTTP_200_OK)


@extend_schema_view(
    list=extend_schema(
        summary="Get system logs",
        description="Return system log lines with limit and offset support.",
        parameters=[
            OpenApiParameter(
                name="limit",
                type=int,
                location=OpenApiParameter.QUERY,
                description="Number of log lines to return (default: 100, max: 1000).",
                required=False,
            ),
            OpenApiParameter(
                name="offset",
                type=int,
                location=OpenApiParameter.QUERY,
                description="Number of log lines to offset from the end of the log file.",
                required=False,
            ),
        ],
        responses={200: OpenApiTypes.OBJECT},
    )
)
class LogLogsViewSet(viewsets.ViewSet):
    permission_classes = [IsAnAdminUser]

    def list(self, request):
        """
        Return system log lines with limit and offset support.
        """
        limit = request.query_params.get("limit", 100)
        offset = request.query_params.get("offset", 0)
        try:
            limit = int(limit)
        except ValueError:
            limit = 100

        try:
            offset = int(offset)
        except ValueError:
            offset = 0

        if limit <= 0 or limit > 1000:
            limit = 100

        if offset < 0:
            offset = 0

        log_file = settings.BASE_DIR / "logs/system.log"
        if not log_file.exists():
            return Response({"error": "Log file not found"}, status=404)

        try:
            with open(log_file, "r") as f:
                lines = f.readlines()
                total = len(lines)
                end = total - offset if offset < total else total
                start = max(0, end - limit)
                slice_lines = lines[start:end]
            return Response({
                "count": total,
                "limit": limit,
                "offset": offset,
                "logs": slice_lines,
            })
        except Exception as e:
            return Response({"error": str(e)}, status=500)


class AuditLogLimitOffsetPagination(LimitOffsetPagination):
    default_limit = 100
    max_limit = 1000


audit_log_parameters = [
    OpenApiParameter(
        name="limit",
        type=int,
        location=OpenApiParameter.QUERY,
        description="Number of results to return per page (default: 100, max: 1000).",
        required=False,
    ),
    OpenApiParameter(
        name="offset",
        type=int,
        location=OpenApiParameter.QUERY,
        description="The initial index from which to return the results.",
        required=False,
    ),
    OpenApiParameter(
        name="action",
        type=str,
        location=OpenApiParameter.QUERY,
        description="Filter by action type: 'create' (0), 'update' (1), 'delete' (2), or 'access' (3).",
        required=False,
    ),
    OpenApiParameter(
        name="model",
        type=str,
        location=OpenApiParameter.QUERY,
        description="Filter by target model name (case-insensitive, e.g. 'device', 'user', 'machine').",
        required=False,
    ),
    OpenApiParameter(
        name="app",
        type=str,
        location=OpenApiParameter.QUERY,
        description="Filter by Django app label (e.g. 'users', 'infrastructure', 'roles').",
        required=False,
    ),
    OpenApiParameter(
        name="actor",
        type=str,
        location=OpenApiParameter.QUERY,
        description="Filter by actor ID (integer) or actor email address (substring match).",
        required=False,
    ),
    OpenApiParameter(
        name="object_pk",
        type=str,
        location=OpenApiParameter.QUERY,
        description="Filter by primary key string of the targeted object.",
        required=False,
    ),
    OpenApiParameter(
        name="start_date",
        type=str,
        location=OpenApiParameter.QUERY,
        description="Filter log entries on or after this ISO 8601 date/datetime (e.g. '2026-01-01T00:00:00Z').",
        required=False,
    ),
    OpenApiParameter(
        name="end_date",
        type=str,
        location=OpenApiParameter.QUERY,
        description="Filter log entries on or before this ISO 8601 date/datetime (e.g. '2026-08-06T23:59:59Z').",
        required=False,
    ),
    OpenApiParameter(
        name="search",
        type=str,
        location=OpenApiParameter.QUERY,
        description="Free-text search matching object representation, field changes, actor details, or action details.",
        required=False,
    ),
]


@extend_schema_view(
    list=extend_schema(
        summary="List global audit logs",
        description=(
            "Retrieves a paginated list of system audit log entries for global admins and superusers. "
            "Supports limit/offset pagination and multi-field filtering by action type, target model/app, actor, "
            "object primary key, date ranges, and keyword search."
        ),
        parameters=audit_log_parameters,
        responses={200: LogEntrySerializer(many=True)},
    ),
    retrieve=extend_schema(
        summary="Retrieve specific audit log entry",
        description="Retrieves a single audit log entry by its unique database ID.",
        responses={200: LogEntrySerializer},
    ),
    get_tenant_admin_logs=extend_schema(
        summary="Get tenant admin audit logs",
        description=(
            "Retrieves audit logs filtered specifically for the requester's tenant. "
            "Superusers retrieve all logs. Supports limit/offset pagination and query parameter filters."
        ),
        parameters=audit_log_parameters,
        responses={200: LogEntrySerializer(many=True)},
    ),
)
class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing audit logs with query parameter filtering and limit/offset pagination.
    """

    queryset = LogEntry.objects.all().order_by("-timestamp")
    serializer_class = LogEntrySerializer
    permission_classes = [IsAnAdminUser]
    pagination_class = AuditLogLimitOffsetPagination

    def filter_audit_queryset(self, queryset, request):
        params = request.query_params

        # Filter by action (0=CREATE, 1=UPDATE, 2=DELETE, 3=ACCESS)
        action_param = params.get("action")
        if action_param is not None:
            action_map = {"create": 0, "update": 1, "delete": 2, "access": 3}
            val = action_map.get(str(action_param).lower(), action_param)
            if str(val).isdigit():
                queryset = queryset.filter(action=int(val))

        # Filter by model name
        model_param = params.get("model")
        if model_param:
            queryset = queryset.filter(content_type__model__iexact=model_param)

        # Filter by app label
        app_param = params.get("app")
        if app_param:
            queryset = queryset.filter(content_type__app_label__iexact=app_param)

        # Filter by actor (ID, username, or email)
        actor_param = params.get("actor")
        if actor_param:
            queryset = queryset.filter(
                Q(actor_id=actor_param)
                | Q(actor__username__iexact=actor_param)
                | Q(actor__email__icontains=actor_param)
            )

        # Filter by object_pk
        object_pk = params.get("object_pk")
        if object_pk:
            queryset = queryset.filter(object_pk=str(object_pk))

        # Filter by date range
        start_date = params.get("start_date") or params.get("from_date")
        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)

        end_date = params.get("end_date") or params.get("to_date")
        if end_date:
            queryset = queryset.filter(timestamp__lte=end_date)

        # Search filter
        search = params.get("search")
        if search:
            queryset = queryset.filter(
                Q(object_repr__icontains=search)
                | Q(changes__icontains=search)
                | Q(actor__username__icontains=search)
                | Q(actor__email__icontains=search)
                | Q(additional_data__icontains=search)
            )

        return queryset

    def get_queryset(self):
        queryset = LogEntry.objects.all().order_by("-timestamp")
        return self.filter_audit_queryset(queryset, self.request)

    @action(detail=False, methods=["get"], permission_classes=[IsTenantAdminUser])
    def get_tenant_admin_logs(self, request):
        """
        Return audit logs for tenant admins.
        Filters logs where the actor belongs to the same tenant as the requester or parent_tenant_id matches.
        """
        user = request.user

        if user.is_superuser:
            queryset = LogEntry.objects.all().order_by("-timestamp")
        else:
            if getattr(user, "tenant", None):
                queryset = LogEntry.objects.filter(
                    Q(actor__tenant=user.tenant)
                    | Q(additional_data__parent_tenant_id=str(user.tenant.id))
                ).order_by("-timestamp")
            else:
                queryset = LogEntry.objects.none()

        queryset = self.filter_audit_queryset(queryset, request)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class OTPRequestView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Authentication - OTP"],
        summary="Request / Resend 2FA Email OTP",
        description=(
            "### Instructions for Integration:\n"
            "1. Client posts an active user's `username`.\n"
            "2. The server generates a cryptographically random 6-digit numeric OTP code (valid for **5 minutes**) uniquely bound to this username.\n"
            "3. The code is dispatched via email (Mailgun) to the user's registered address.\n\n"
            "**Note**: Only active, pre-registered user accounts can request an OTP. "
            "If the username does not exist or is inactive, an HTTP 400 validation error is returned."
        ),
        request=OTPRequestSerializer,
        examples=[
            OpenApiExample(
                "Request OTP Example",
                value={"username": "user123"},
                request_only=True,
            ),
            OpenApiExample(
                "Request OTP Success Response",
                value={"detail": "Verification code sent to email."},
                response_only=True,
                status_codes=["200"],
            ),
            OpenApiExample(
                "User Not Found Error Response",
                value={"username": ["No active account found with this username."]},
                response_only=True,
                status_codes=["400"],
            ),
        ],
        responses={
            200: OpenApiResponse(
                description="OTP verification code successfully sent to email.",
                response=inline_serializer(
                    name="OTPRequestSuccessResponse",
                    fields={"detail": serializers.CharField()},
                ),
            ),
            400: OpenApiResponse(
                description="Invalid input or active user account not found.",
                response=OpenApiTypes.OBJECT,
            ),
            500: OpenApiResponse(
                description="Internal server error sending email.",
                response=OpenApiTypes.OBJECT,
            ),
        },
    )
    def post(self, request, *args, **kwargs):
        serializer = OTPRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        username = serializer.validated_data["username"]
        user = User.objects.get(username__iexact=username, is_active=True)

        # Generate a cryptographically secure 6-digit OTP code
        otp_code = f"{secrets.randbelow(1000000):06d}"

        # Store in cache for 5 minutes (300 seconds) uniquely tied to this username
        cache_key = f"otp_data_{user.username.lower()}"
        cache.set(
            cache_key,
            {
                "code": otp_code,
                "attempts": 0,
                "user_id": str(user.id),
                "username": user.username.lower(),
            },
            timeout=300,
        )

        try:
            send_otp_email(user, otp_code)
        except Exception as e:
            logger.error(f"Failed to send OTP email to {user.email}: {str(e)}")
            return Response(
                {"detail": "Error sending OTP email. Please try again later."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        logger.info(f"🔑 OTP requested and sent to {user.email} for username {user.username}")
        return Response(
            {"detail": "Verification code sent to email."},
            status=status.HTTP_200_OK,
        )


class OTPVerifyView(APIView):
    permission_classes = [AllowAny]

    @method_decorator(conditional_csrf_protect)
    @extend_schema(
        tags=["Authentication - OTP"],
        summary="Verify Email OTP and Obtain JWT Tokens",
        description=(
            "### Instructions for Integration:\n"
            "1. Client posts the `username` and the 6-digit `code` received in their inbox.\n"
            "2. The server verifies the OTP code specifically tied to that username in cache.\n"
            "3. **Attempt Limit**: Up to 3 incorrect attempts are allowed before the OTP code is permanently invalidated.\n"
            "4. **Account Binding**: Codes are strictly bound to the individual account and cannot be used across different accounts.\n"
            "5. On successful verification:\n"
            "   - The OTP code is deleted from cache.\n"
            "   - The JWT `access` token is returned in the JSON response body.\n"
            "   - The JWT `refresh_token` is set in an HTTP-Only secure cookie (`REFRESH_COOKIE_NAME`).\n\n"
            "**Web Browser CSRF Protection**: Standard conditional CSRF protection applies for web clients."
        ),
        request=OTPVerifySerializer,
        examples=[
            OpenApiExample(
                "Verify OTP Request Example",
                value={"username": "user123", "code": "123456"},
                request_only=True,
            ),
            OpenApiExample(
                "Verify OTP Success Response",
                value={"access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."},
                response_only=True,
                status_codes=["200"],
            ),
            OpenApiExample(
                "Invalid Code Error Response",
                value={"detail": "Invalid verification code. 2 attempt(s) remaining."},
                response_only=True,
                status_codes=["400"],
            ),
            OpenApiExample(
                "Expired OTP Error Response",
                value={"detail": "OTP expired or not requested. Please request a new code."},
                response_only=True,
                status_codes=["400"],
            ),
        ],
        responses={
            200: OpenApiResponse(
                description="OTP verified successfully. Returns JWT access token in body and sets HTTP-only refresh cookie.",
                response=inline_serializer(
                    name="OTPVerifySuccessResponse",
                    fields={"access": serializers.CharField()},
                ),
            ),
            400: OpenApiResponse(
                description="Invalid OTP code, expired code, or maximum attempts exceeded.",
                response=OpenApiTypes.OBJECT,
            ),
        },
    )
    def post(self, request, *args, **kwargs):
        serializer = OTPVerifySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        username = serializer.validated_data["username"].strip().lower()
        input_code = serializer.validated_data["code"].strip()

        cache_key = f"otp_data_{username}"
        otp_data = cache.get(cache_key)

        if not otp_data:
            return Response(
                {"detail": "OTP expired or not requested. Please request a new code."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Ensure the code is strictly linked to this unique account
        if otp_data.get("username") != username:
            return Response(
                {"detail": "Invalid verification code for this account."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if otp_data["attempts"] >= 3:
            cache.delete(cache_key)
            return Response(
                {"detail": "Too many invalid attempts. Please request a new OTP."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if otp_data["code"] != input_code:
            otp_data["attempts"] += 1
            remaining = 3 - otp_data["attempts"]
            if remaining > 0:
                cache.set(cache_key, otp_data, timeout=300)
                return Response(
                    {"detail": f"Invalid verification code. {remaining} attempt(s) remaining."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            else:
                cache.delete(cache_key)
                return Response(
                    {"detail": "Too many invalid attempts. Please request a new OTP."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Clear OTP from cache after successful verification
        cache.delete(cache_key)

        try:
            user = User.objects.get(id=otp_data["user_id"], is_active=True)
        except User.DoesNotExist:
            return Response(
                {"detail": "Active user account not found."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verify that the account retrieved matches the requested username
        if user.username.lower() != username:
            return Response(
                {"detail": "Account mismatch."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Generate tokens using CustomTokenObtainPairSerializer logic
        refresh = RefreshToken.for_user(user)

        # Apply custom claims from CustomTokenObtainPairSerializer
        token_data = CustomTokenObtainPairSerializer.get_token(user)
        for claim_key in ["user_id", "username", "is_global", "cs_tenant_id", "is_superuser", "is_support", "is_tenant_admin"]:
            if claim_key in token_data:
                refresh[claim_key] = token_data[claim_key]

        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        response = Response(
            {"access": access_token},
            status=status.HTTP_200_OK,
        )

        refresh_lifetime = settings.SIMPLE_JWT.get("REFRESH_TOKEN_LIFETIME")
        if not isinstance(refresh_lifetime, timedelta):
            refresh_lifetime = timedelta(days=1)
        max_age = int(refresh_lifetime.total_seconds())

        response.set_cookie(
            key=REFRESH_COOKIE_NAME,
            value=refresh_token,
            max_age=max_age,
            httponly=True,
            secure=settings.COOKIE_SECURE,
            samesite="Lax",
            path=REFRESH_COOKIE_PATH,
        )

        logger.info(f"✅ User {user.username} logged in via Email OTP")
        return response


