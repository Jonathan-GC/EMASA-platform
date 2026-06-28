from .serializers import (
    UserSerializer,
    UserMeSerializer,
    CustomTokenObtainPairSerializer,
    CustomTokenRefreshSerializer,
    LogEntrySerializer,
)
from .models import User, OAuthAccount
from roles.permissions import HasPermission
from auditlog.models import LogEntry

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
from rest_framework import status, viewsets
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken

from drf_spectacular.utils import (
    extend_schema_view,
    extend_schema,
    OpenApiExample,
    OpenApiResponse,
)
from drf_spectacular.types import OpenApiTypes

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

from roles.permissions import IsAnAdminUser, IsTenantAdminUser

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

    @method_decorator(conditional_csrf_protect)
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
            {
                "name": "redirect_uri",
                "in_": "query",
                "description": (
                    "Optional override for the OAuth redirect URI. "
                    "Must belong to ``GOOGLE_ALLOWED_REDIRECT_URIS``."
                ),
                "schema": {"type": "string"},
            }
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

        redirect_uri = resolved if resolved is not None else settings.GOOGLE_REDIRECT_URI

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
    or creates a new account with a linked OAuthAccount.
    """

    permission_classes = [AllowAny]

    @method_decorator(csrf_protect)
    @extend_schema(
        summary="Google OAuth2 callback",
        description=(
            "Exchanges the authorization `code` the frontend received from "
            "Google for an ID token, validates it, and either logs the user "
            "in (if a matching `OAuthAccount` exists) or creates a brand-new "
            "account.\n\n"
            "If an account with the same email **already exists** but has no "
            "linked Google identity the endpoint returns **409 Conflict** — "
            "the user must log in with their password and link the Google "
            "account via the `auth/google/link/` endpoint."
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
            409: OpenApiResponse(
                description=(
                    "An account with this email already exists but has no "
                    "linked Google identity.  The frontend should prompt the "
                    "user to log in and link their account."
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
                "Email already exists",
                value={
                    "detail": (
                        "An account with this email already exists. "
                        "Please log in with your password and link your "
                        "Google account in settings."
                    ),
                    "code": "email_exists",
                    "email": "user@example.com",
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
        redirect_uri = resolved if resolved is not None else settings.GOOGLE_REDIRECT_URI

        idinfo = self._exchange_and_verify(code, redirect_uri)
        if isinstance(idinfo, Response):
            return idinfo

        email = idinfo.get("email")
        sub = idinfo.get("sub")

        if not email or not sub:
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
            try:
                existing_user = User.objects.get(email=email)
                return Response(
                    {
                        "detail": (
                            "An account with this email already exists. "
                            "Please log in with your password and link your "
                            "Google account in settings."
                        ),
                        "code": "email_exists",
                        "email": email,
                    },
                    status=status.HTTP_409_CONFLICT,
                )
            except User.DoesNotExist:
                user = self._create_user_from_google(idinfo, sub, email)

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
            idinfo = id_token.verify_oauth2_token(
                google_id_token, requests.Request()
            )
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

    def _create_user_from_google(self, idinfo, sub, email):
        base_username = email.split("@")[0]
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}_{counter}"
            counter += 1

        user = User.objects.create(
            username=username,
            email=email,
            name=idinfo.get("given_name", ""),
            last_name=idinfo.get("family_name", ""),
            is_active=True,
        )
        user.set_unusable_password()
        user.save()

        OAuthAccount.objects.create(
            user=user,
            provider="google",
            provider_user_id=sub,
            email=email,
        )

        assign_new_user_base_permissions(user)
        return user

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
        redirect_uri = resolved if resolved is not None else settings.GOOGLE_REDIRECT_URI

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
            idinfo = id_token.verify_oauth2_token(
                google_id_token, requests.Request()
            )
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
                {
                    "detail": "This Google account is already linked to another user."
                },
                status=status.HTTP_409_CONFLICT,
            )

        OAuthAccount.objects.create(
            user=request.user,
            provider="google",
            provider_user_id=sub,
            email=email,
        )

        return Response({"detail": "Google account linked successfully."})


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


@extend_schema_view(
    list=extend_schema(
        description="Get system logs", responses={200: OpenApiTypes.OBJECT}
    )
)
class LogLogsViewSet(viewsets.ViewSet):
    permission_classes = [IsAnAdminUser]

    def list(self, request):
        """
        Return the last 100 lines of the system log.
        """
        limit = request.query_params.get("limit", 100)
        try:
            limit = int(limit)
        except ValueError:
            limit = 100

        if limit <= 0 or limit > 1000:
            limit = 100

        log_file = settings.BASE_DIR / "logs/system.log"
        if not log_file.exists():
            return Response({"error": "Log file not found"}, status=404)

        try:
            with open(log_file, "r") as f:
                # Read all lines and take the last 100
                lines = f.readlines()[-limit:]
            return Response({"logs": lines})
        except Exception as e:
            return Response({"error": str(e)}, status=500)


@extend_schema_view(
    list=extend_schema(description="Audit Log List"),
    retrieve=extend_schema(description="Audit Log Retrieve"),
)
class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing audit logs.
    """

    queryset = LogEntry.objects.all().order_by("-timestamp")
    serializer_class = LogEntrySerializer
    permission_classes = [IsAnAdminUser]

    @action(detail=False, methods=["get"], permission_classes=[IsTenantAdminUser])
    def get_tenant_admin_logs(self, request):
        """
        Return audit logs for tenant admins.
        Filters logs where the actor belongs to the same tenant as the requester.
        """
        user = request.user

        if user.is_superuser:
            queryset = LogEntry.objects.all().order_by("-timestamp")
        else:
            queryset = LogEntry.objects.filter(actor__tenant=user.tenant).order_by(
                "-timestamp"
            )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
