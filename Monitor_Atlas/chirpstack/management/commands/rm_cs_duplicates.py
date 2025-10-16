from django.core.management.base import BaseCommand
from django.db.models import Count
from chirpstack.models import DeviceProfile
from organizations.models import Tenant
from chirpstack.chirpstack_api import (
    CHIRPSTACK_DEVICE_PROFILE_URL,
    CHIRPSTACK_TENANT_URL,
    HEADERS,
    sync_device_profile_destroy,
)
import requests
from loguru import logger


class Command(BaseCommand):
    help = "Remove duplicate device profiles from Chirpstack and update local DB"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be deleted without actually deleting",
        )
        parser.add_argument(
            "--tenant-id",
            type=str,
            help="Only process device profiles for specific tenant ID",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        tenant_id_filter = options.get("tenant_id")

        self.stdout.write(
            self.style.WARNING(
                f"Starting duplicate removal {'(DRY RUN)' if dry_run else ''}"
            )
        )

        # Obtener lista de tenants
        if tenant_id_filter:
            # Si se especifica un tenant, usar solo ese
            tenant_ids = [tenant_id_filter]
        else:
            # Obtener todos los tenants de la base de datos local
            tenants = Tenant.objects.exclude(cs_tenant_id__isnull=True).exclude(
                cs_tenant_id=""
            )
            tenant_ids = [t.cs_tenant_id for t in tenants]

            if not tenant_ids:
                self.stdout.write(
                    self.style.WARNING("No tenants found with Chirpstack IDs")
                )
                return

        self.stdout.write(self.style.SUCCESS(f"Processing {len(tenant_ids)} tenant(s)"))

        # Recopilar todos los device profiles por tenant
        all_profiles = []
        for tenant_id in tenant_ids:
            response = requests.get(
                CHIRPSTACK_DEVICE_PROFILE_URL,
                headers=HEADERS,
                params={"limit": 1000, "tenantId": tenant_id},
            )

            if response.status_code != 200:
                self.stdout.write(
                    self.style.ERROR(
                        f"Error fetching device profiles for tenant {tenant_id}: {response.text}"
                    )
                )
                continue

            profiles = response.json().get("result", [])
            self.stdout.write(
                f"  Tenant {tenant_id}: found {len(profiles)} device profile(s)"
            )
            all_profiles.extend(profiles)

        if not all_profiles:
            self.stdout.write(self.style.WARNING("No device profiles found"))
            return

        # Agrupar por nombre y tenant
        profiles_by_name = {}
        for profile in all_profiles:
            name = profile["name"]
            tenant = profile.get("tenantId", "unknown")
            key = f"{name}|{tenant}"

            if key not in profiles_by_name:
                profiles_by_name[key] = []
            profiles_by_name[key].append(profile)

        # Procesar duplicados
        total_duplicates = 0
        total_deleted = 0

        for key, profiles in profiles_by_name.items():
            if len(profiles) <= 1:
                continue

            total_duplicates += len(profiles) - 1
            name, tenant = key.split("|")

            self.stdout.write(
                self.style.WARNING(
                    f"\nFound {len(profiles)} profiles with name '{name}' in tenant {tenant}"
                )
            )

            # Ordenar por fecha de creación (más antiguo primero)
            profiles_sorted = sorted(
                profiles, key=lambda x: x.get("createdAt", x["id"])
            )

            # Mantener el primero (más antiguo)
            keeper = profiles_sorted[0]
            to_delete = profiles_sorted[1:]

            self.stdout.write(
                self.style.SUCCESS(f"  Keeping: {keeper['name']} (ID: {keeper['id']})")
            )

            # Actualizar referencias locales al perfil que se mantiene
            local_profile = DeviceProfile.objects.filter(
                cs_device_profile_id=keeper["id"]
            ).first()

            if not local_profile:
                # Si no existe localmente, buscar uno que tenga el mismo nombre
                local_profile = DeviceProfile.objects.filter(
                    name=keeper["name"], workspace__tenant__cs_tenant_id=tenant
                ).first()

                if local_profile:
                    local_profile.cs_device_profile_id = keeper["id"]
                    if not dry_run:
                        local_profile.save()
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  Updated local profile to use ID: {keeper['id']}"
                        )
                    )

            # Eliminar duplicados
            for dup in to_delete:
                self.stdout.write(
                    self.style.WARNING(f"  Deleting: {dup['name']} (ID: {dup['id']})")
                )

                # Reasignar dispositivos que usan este perfil
                devices_using_dup = self._get_devices_using_profile(dup["id"], tenant)
                if devices_using_dup:
                    self.stdout.write(
                        f"    Found {len(devices_using_dup)} devices using this profile"
                    )
                    if not dry_run:
                        self._reassign_devices(devices_using_dup, keeper["id"])

                # Actualizar referencias locales que apunten al duplicado
                local_dups = DeviceProfile.objects.filter(
                    cs_device_profile_id=dup["id"]
                )

                for local_dup in local_dups:
                    if local_profile and local_profile.id != local_dup.id:
                        # Reasignar dispositivos locales
                        from infrastructure.models import Device

                        devices_count = Device.objects.filter(
                            device_profile=local_dup
                        ).count()
                        if devices_count > 0:
                            self.stdout.write(
                                f"    Reassigning {devices_count} local devices"
                            )
                            if not dry_run:
                                Device.objects.filter(device_profile=local_dup).update(
                                    device_profile=local_profile
                                )

                        if not dry_run:
                            self.stdout.write(
                                f"    Deleting local duplicate: {local_dup.id}"
                            )
                            local_dup.delete()
                    else:
                        local_dup.cs_device_profile_id = keeper["id"]
                        if not dry_run:
                            local_dup.save()

                # Eliminar de Chirpstack
                if not dry_run:
                    delete_response = requests.delete(
                        f"{CHIRPSTACK_DEVICE_PROFILE_URL}/{dup['id']}", headers=HEADERS
                    )
                    if delete_response.status_code == 200:
                        total_deleted += 1
                        self.stdout.write(
                            self.style.SUCCESS(f"    ✓ Deleted from Chirpstack")
                        )
                    else:
                        self.stdout.write(
                            self.style.ERROR(
                                f"    ✗ Error deleting: {delete_response.text}"
                            )
                        )

        # Resumen
        self.stdout.write(
            self.style.SUCCESS(
                f"\n{'Would delete' if dry_run else 'Deleted'} {total_duplicates} duplicate profiles"
            )
        )
        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully deleted {total_deleted} profiles from Chirpstack"
                )
            )

    def _get_devices_using_profile(self, profile_id, tenant_id):
        """Get devices using a specific device profile from Chirpstack"""
        from chirpstack.chirpstack_api import CHIRPSTACK_DEVICE_URL

        response = requests.get(
            CHIRPSTACK_DEVICE_URL,
            headers=HEADERS,
            params={
                "limit": 1000,
                "deviceProfileId": profile_id,
                "tenantId": tenant_id,
            },
        )

        if response.status_code == 200:
            return response.json().get("result", [])
        return []

    def _reassign_devices(self, devices, new_profile_id):
        """Reassign devices to a new device profile"""
        from chirpstack.chirpstack_api import CHIRPSTACK_DEVICE_URL

        for device in devices:
            payload = {"device": {**device, "deviceProfileId": new_profile_id}}

            response = requests.put(
                f"{CHIRPSTACK_DEVICE_URL}/{device['devEui']}",
                headers=HEADERS,
                json=payload,
            )

            if response.status_code == 200:
                logger.info(
                    f"Reassigned device {device['devEui']} to profile {new_profile_id}"
                )
            else:
                logger.error(
                    f"Error reassigning device {device['devEui']}: {response.text}"
                )
