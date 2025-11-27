from django.core.management.base import BaseCommand
from django.apps import apps
from django.db import transaction

from roles.global_helpers import (
    set_base_global_add_permissions,
    apply_staff_permissions,
    GLOBAL_PERMISSIONS_PRESET,
)


class Command(BaseCommand):
    help = "Configura permisos globales y permisos por objeto después del seed."

    @transaction.atomic
    def handle(self, *args, **options):

        self.stdout.write(self.style.WARNING("Asignando permisos globales base..."))
        set_base_global_add_permissions()
        self.stdout.write(self.style.SUCCESS("✔ Permisos globales asignados."))

        self.stdout.write(self.style.WARNING("Asignando permisos por objeto..."))

        # Recorremos todos los modelos usados en la matriz de permisos
        modelos_procesados = set()

        for role, apps_models in GLOBAL_PERMISSIONS_PRESET.items():
            for app_label, model_list in apps_models.items():
                for model_name in model_list:

                    key = f"{app_label}.{model_name}"
                    if key in modelos_procesados:
                        continue
                    modelos_procesados.add(key)

                    try:
                        model = apps.get_model(app_label, model_name)
                    except LookupError:
                        self.stdout.write(
                            self.style.ERROR(
                                f"❌ Modelo no encontrado: {app_label}.{model_name}"
                            )
                        )
                        continue

                    # Cargar todas las instancias del modelo
                    queryset = model.objects.all()

                    if queryset.count() == 0:
                        continue

                    self.stdout.write(
                        f" → Procesando {queryset.count()} objetos de {app_label}.{model_name}"
                    )

                    for obj in queryset:
                        apply_staff_permissions(obj)

        self.stdout.write(
            self.style.SUCCESS("✔ Permisos por objeto asignados correctamente.")
        )
        self.stdout.write(self.style.SUCCESS("🎉 Setup de permisos completado."))
