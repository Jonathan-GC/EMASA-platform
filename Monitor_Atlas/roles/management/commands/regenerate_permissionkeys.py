from django.core.management.base import BaseCommand
from django.apps import apps
from roles.models import PermissionKey

# Mapeo de scopes a los nombres de campo en PermissionKey
SCOPE_MODEL_MAP = {
    "device": "device_id",
    "machine": "machine_id",
    "application": "application_id",
    "user": "user_id",
    "role": "role_id",
    "workspace": "workspace_id",
    "tenant": "tenant_id",
    "location": "location_id",
    "gateway": "gateway_id",
    "device_profile": "device_profile_id",
    "device_profile_template": "device_profile_template_id",
    "api_user": "api_user_id",
    "type": "type_id",
    "subscription": "subscription_id",
}

APP_LABEL_MAP = {
    "device": "infrastructure",
    "machine": "infrastructure",
    "application": "infrastructure",
    "user": "users",
    "role": "roles",
    "workspace": "organizations",
    "tenant": "organizations",
    "location": "infrastructure",
    "gateway": "infrastructure",
    "device_profile": "chirpstack",
    "device_profile_template": "chirpstack",
    "api_user": "chirpstack",
    "type": "infrastructure",
    "subscription": "organizations",
}

MODEL_CLASS_MAP = {
    "device_profile": "DeviceProfile",
    "device_profile_template": "DeviceProfileTemplate",
    "api_user": "ApiUser",
    # add others if needed
}


class Command(BaseCommand):
    help = "Regenerates all PermissionKeys for all registered models."

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("⛔ Deleting existent PermissionKeys..."))
        PermissionKey.objects.all().delete()

        total = 0

        for scope, field_name in SCOPE_MODEL_MAP.items():
            app_label = APP_LABEL_MAP.get(scope)
            if not app_label:
                self.stdout.write(
                    self.style.NOTICE(f"⚠ Scope '{scope}' has no registered model")
                )
                continue
            model_name = MODEL_CLASS_MAP.get(scope, scope.capitalize())
            try:
                model = apps.get_model(app_label, model_name)
            except LookupError:
                self.stdout.write(
                    self.style.NOTICE(f"⚠ Scope '{scope}' has no registered model")
                )
                continue

            self.stdout.write(
                self.style.HTTP_INFO(f" ➕ Processing {scope} ({model.__name__})...")
            )

            for instance in model.objects.all():
                for action in ["get", "post", "put", "delete"]:
                    pk_data = {
                        "code": f"{scope}:{instance.id}:{action}",
                        "scope": scope,
                        "key_type": action,
                        field_name: instance.id,  # Ejemplo: device_id=1
                    }
                    PermissionKey.objects.get_or_create(
                        code=pk_data["code"], defaults=pk_data
                    )
                    total += 1

        self.stdout.write(self.style.SUCCESS(f"✅ Regenerated {total} PermissionKeys"))
