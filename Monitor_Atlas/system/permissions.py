from rest_framework.permissions import BasePermission


class IsSuperUser(BasePermission):
    """
    Permission class that grants access only to authenticated platform superusers.
    """

    def has_permission(self, request, view) -> bool:
        return bool(request.user and request.user.is_authenticated and request.user.is_superuser)
