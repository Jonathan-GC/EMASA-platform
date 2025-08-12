from .serializers import UserSerializer
from .models import User
from roles.permissions import HasPermissionKey
from roles.mixins import PermissionKeyMixin

from rest_framework.viewsets import ModelViewSet

class UserViewSet(ModelViewSet, PermissionKeyMixin):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [HasPermissionKey]
    scope = "user"

    def perform_create(self, serializer):
        instance = serializer.save()
        self.create_permission_keys(instance, scope="user")
