from .serializers import UserSerializer
from .models import User
from roles.permissions import HasPermissionKey, IsAdminOrIsAuthenticatedReadOnly
from roles.mixins import PermissionKeyMixin
from roles.serializers import PermissionKeySerializer
from roles.models import PermissionKey

from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response



class UserViewSet(ModelViewSet, PermissionKeyMixin):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [HasPermissionKey]
    scope = "user"

    def perform_create(self, serializer):
        instance = serializer.save()
        self.create_permission_keys(instance, scope="user")
    
    @action(detail=False, methods=["get"])
    def get_all_permission_keys_by_user(self, request):
        user_id = request.query_params.get("user_id")
        permission_keys = PermissionKey.objects.filter(user_id=user_id)
        serializer = PermissionKeySerializer(permission_keys, many=True)
        return self.get_paginated_response(serializer.data)

        # TODO: CORREGIR
    
    @action(detail=True, methods=["post"], permission_classes=[IsAdminOrIsAuthenticatedReadOnly])
    def regenerate_permission_keys(self, request, pk=None):
        instance = self.get_object()
        scope = "user"

        self.create_permission_keys(instance, scope)

        permission_keys = PermissionKey.objects.filter(
            **{self.scope_field_map[scope]: instance}
        )
        serializer = PermissionKeySerializer(permission_keys, many=True)

        return Response(serializer.data)

    @action(detail=True, methods=["patch"], permission_classes=[HasPermissionKey])
    def set_user_image(self, request, pk=None):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    @action (detail=True, methods=["patch"], permission_classes=[HasPermissionKey])
    def disable_user(self, request, pk=None):
        instance = self.get_object()
        instance.is_active = False
        instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action (detail=True, methods=["patch"], permission_classes=[HasPermissionKey])
    def enable_user(self, request, pk=None):
        instance = self.get_object()
        instance.is_active = True
        instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)