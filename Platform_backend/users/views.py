from django.shortcuts import render

from .serializers import UserSerializer
from .models import User
from roles.permissions import PermissionKey

from rest_framework import viewsets

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [PermissionKey]
    scope = "user"
    