from django.shortcuts import render

from .models import Workspace, Organization, Region
from .serializers import WorkspaceSerializer, OrganizationSerializer, RegionSerializer

from roles.permissions import IsAdminOrIsAuthenticatedReadOnly, HasPermissionKey

from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser

class WorkspaceViewSet(viewsets.ModelViewSet):
    queryset = Workspace.objects.all()
    serializer_class = WorkspaceSerializer
    permission_classes = [HasPermissionKey]
    scope = "workspace"


class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = [IsAdminOrIsAuthenticatedReadOnly]


class RegionViewSet(viewsets.ModelViewSet):
    queryset = Region.objects.all()
    serializer_class = RegionSerializer
    permission_classes = [HasPermissionKey]
    scope = "region"


