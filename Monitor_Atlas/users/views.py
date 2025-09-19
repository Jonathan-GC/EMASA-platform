from .serializers import UserSerializer, CustomTokenObtainPairSerializer
from .models import User
from roles.permissions import HasPermissionKey, IsAdminOrIsAuthenticatedReadOnly
from roles.mixins import PermissionKeyMixin
from roles.serializers import PermissionKeySerializer
from roles.models import PermissionKey

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
REFRESH_COOKIE_NAME = "refresh_token"
REFRESH_COOKIE_PATH = "/"


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


@ensure_csrf_cookie
@api_view(["GET"])
@permission_classes([AllowAny])
def csrf_setup(request):
    return Response({"detail": "CSRF cookie set."}, status=status.HTTP_200_OK)
