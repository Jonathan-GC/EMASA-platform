from django.core.management.base import BaseCommand
from django.apps import apps
from roles.models import PermissionKey

# Mapeo de scopes a los nombres de campo en PermissionKey
SCOPE_MODEL_MAP = {
    'device': 'device_id',
    'machine': 'machine_id',
    'application': 'application_id',
    'user': 'user_id',
    'role': 'role_id',
    'workspace': 'workspace_id',
    'tenant': 'tenant_id',
    'location': 'location_id',
    'gateway': 'gateway_id',
    'device_profile': 'device_profile_id',
    'device_profile_template': 'device_profile_template_id',
    'api_user': 'api_user_id',
    'type': 'type_id',
    'subscription': 'subscription_id',
}

class Command(BaseCommand):
    help = "Regenera todas las PermissionKeys para todos los modelos registrados."

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Eliminando PermissionKeys existentes..."))
        PermissionKey.objects.all().delete()

        total = 0

        for scope, field_name in SCOPE_MODEL_MAP.items():
            # Obtener el modelo dinámicamente según el scope
            try:
                model = apps.get_model("apps.infrastructure", scope.capitalize())  # ajustar si los modelos no están todos en infrastructure
            except LookupError:
                try:
                    model = apps.get_model("apps.roles", scope.capitalize())
                except LookupError:
                    try:
                        model = apps.get_model("apps.users", scope.capitalize())
                    except LookupError:
                        self.stdout.write(self.style.NOTICE(f"⚠ Scope '{scope}' no tiene modelo registrado"))
                        continue

            self.stdout.write(self.style.WARNING(f"Procesando {scope} ({model.__name__})..."))

            for instance in model.objects.all():
                for action in ["create", "read", "update", "delete"]:
                    pk_data = {
                        "code": f"{scope}:{instance.id}:{action}",
                        "scope": scope,
                        "key_type": action,
                        field_name: instance.id,  # Ejemplo: device_id=1
                    }
                    PermissionKey.objects.get_or_create(
                        code=pk_data["code"],
                        defaults=pk_data
                    )
                    total += 1

        self.stdout.write(self.style.SUCCESS(f"✅ Regeneradas {total} PermissionKeys"))