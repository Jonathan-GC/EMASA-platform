from .serializers import UserSerializer, CustomTokenObtainPairSerializer
from .models import User
from roles.permissions import HasPermissionKey
from roles.mixins import PermissionKeyMixin

from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response


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

from google.oauth2 import id_token
from google.auth.transport import requests

from .emails import (
    send_verification_email,
    send_password_reset_email,
    send_password_reset_email_with_template,
)
from .jwt import generate_token, verify_token

# User ViewSet


@extend_schema_view(
    list=extend_schema(description="User List"),
    create=extend_schema(description="User Create"),
    retrieve=extend_schema(description="User Retrieve"),
    update=extend_schema(description="User Update"),
    partial_update=extend_schema(description="User Partial Update"),
    destroy=extend_schema(description="User Destroy"),
    set_user_image=extend_schema(description="Set user image"),
    disable_user=extend_schema(description="Disable a user"),
    enable_user=extend_schema(description="Enable a user"),
)
class UserViewSet(ModelViewSet, PermissionKeyMixin):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [HasPermissionKey]
    scope = "user"

    def perform_create(self, serializer):
        instance = serializer.save()
        self.create_permission_keys(instance, scope="user")

    @action(detail=True, methods=["patch"], permission_classes=[HasPermissionKey])
    def set_user_image(self, request, pk=None):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=True, methods=["patch"], permission_classes=[HasPermissionKey])
    def disable_user(self, request, pk=None):
        instance = self.get_object()
        instance.is_active = False
        instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=True, methods=["patch"], permission_classes=[HasPermissionKey])
    def enable_user(self, request, pk=None):
        instance = self.get_object()
        instance.is_active = True
        instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


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


class RegisterView(APIView, PermissionKeyMixin):
    permission_classes = [AllowAny]

    @method_decorator(csrf_protect)
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save(is_active=False)

            self.create_permission_keys(user, scope="user")

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

        send_password_reset_email_with_template(user, token)

        return Response(
            {"detail": "If the email is registered, a reset link has been sent."},
            status=200,
        )


class AccountVerificationView(APIView):
    permission_classes = [AllowAny]

    @method_decorator(csrf_protect)
    def post(self, request):
        token = request.data.get("token")
        if not token:
            return Response({"detail": "Token is required."}, status=400)

        try:
            payload = verify_token(token, scope="verify_email")
            user_id = payload.get("user_id")
            user = User.objects.get(id=user_id)
            user.is_active = True
            user.save()
            return Response({"detail": "Account verified successfully."}, status=200)
        except (ValueError, User.DoesNotExist) as e:
            return Response({"detail": str(e)}, status=400)


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    @method_decorator(csrf_protect)
    def post(self, request):
        token = request.data.get("token")
        new_password = request.data.get("new_password")
        if not token or not new_password:
            return Response(
                {"detail": "Token and new password are required."}, status=400
            )
        try:
            payload = verify_token(token, scope="password_reset")
            user_id = payload.get("user_id")
            user = User.objects.get(id=user_id)
            user.set_password(new_password)
            user.save()
            return Response({"detail": "Password reset successfully."}, status=200)
        except (ValueError, User.DoesNotExist) as e:
            return Response({"detail": str(e)}, status=400)


@ensure_csrf_cookie
@api_view(["GET"])
@permission_classes([AllowAny])
def csrf_setup(request):
    return Response({"detail": "CSRF cookie set."}, status=status.HTTP_200_OK)
