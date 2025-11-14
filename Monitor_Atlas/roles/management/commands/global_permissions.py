from django.core.management.base import BaseCommand
from django.db import transaction

# Importa tu función donde realmente esté
from roles.global_helpers import set_base_global_add_permissions


class Command(BaseCommand):
    help = "Configura los permisos globales base para los roles globales."

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Asignando permisos globales base..."))

        try:
            set_base_global_add_permissions()
            self.stdout.write(
                self.style.SUCCESS("Permisos globales asignados correctamente.")
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error asignando permisos globales: {e}")
            )
            raise e
