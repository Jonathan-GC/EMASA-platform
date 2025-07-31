from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from .serializers import PermissionKeySerializer
from .models import PermissionKey


class PermissionKeyViewSet(viewsets.ModelViewSet):

    queryset = PermissionKey.objects.all()
    serializer_class = PermissionKeySerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
        