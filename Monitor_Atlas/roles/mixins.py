from django.db import transaction
from .models import PermissionKey

class PermissionKeyMixin:
    default_actions = ["get", "get_by_id", "post", "put", "delete"]

    scope_field_map = {
        "machine": "machine",
        "user": "user",
        "role": "role",
        "workspace": "workspace",
        "permission_key": "permission_key",
        "gateway": "gateway",
        "role_permission": "role_permission",
        "device_profile": "device_profile",
        "device_profile_template": "device_profile_template",
        "api_user": "api_user",
        "tenant_user": "tenant_user",
        "type": "type",
        "subscription": "subscription",
        "location": "location",
        "device": "device",
        "application": "application",
        "tenant": "tenant",
    }

    @transaction.atomic
    def create_permission_keys(self, instance, scope):
        """
        Creates permission keys for a given instance and scope.

        This method generates and saves `PermissionKey` objects for the specified `instance`
        and `scope`. It ensures that no duplicate permission keys are created by checking
        existing keys for the instance and only creating new ones for actions not already
        present. The keys are generated based on the default actions and associated with
        the instance using the appropriate field name derived from `scope_field_map`.

        Args:
            instance: The instance for which permission keys are being created.
            scope (str): The scope specifying the type of instance (e.g., "user", "machine").

        Raises:
            ValueError: If the provided `scope` is invalid.

        This method is atomic, ensuring that all database operations within it are completed
        successfully or none at all.
        """

        field_name = self.scope_field_map.get(scope)
        if not field_name:
            raise ValueError(f"Invalid scope: {scope}")

        # Duplicate filter
        existing_keys = set(
            PermissionKey.objects.filter(**{field_name: instance})
            .values_list("key_type", flat=True)
        )

        new_keys = []
        
        for action in self.default_actions:
            if action not in existing_keys:
                # Manually adding code
                code = f"{scope}:{instance.id}:{action}"
                new_keys.append(
                    PermissionKey(
                        scope=scope,
                        key_type=action,
                        code=code,
                        **{field_name: instance},
                    )
                )

        if new_keys:
            PermissionKey.objects.bulk_create(new_keys)