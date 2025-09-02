from chirpstack_api import (
    sync_device_get,
    sync_tenant_get,
    sync_gateway_get,
    sync_api_user_get,
    sync_application_get,
    sync_device_profile_get,
)

from infrastructure.models import Device, Gateway, Application
from chirpstack.models import Tenant, ApiUser, DeviceProfile
from django.core.management.base import BaseCommand
from django.apps import apps
from django.db import transaction
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Sync ChirpStack entities with the database"

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.MIGRATE_HEADING("==> Synchronizing with ChirpStack...")
        )

        with transaction.atomic():
            self.sync_tenants()
            self.sync_gateways()
            self.sync_api_users()
            self.sync_applications()
            self.sync_device_profiles()
            self.sync_devices()

        self.stdout.write(
            self.style.SUCCESS("✅ Initial synchronization with ChirpStack complete.")
        )

    def sync_tenants(self):
        self.stdout.write(self.style.NOTICE("Synchronizing Tenants..."))
        for tenant in Tenant.objects.all():
            try:
                sync_tenant_get(tenant)
                self.stdout.write(
                    self.style.SUCCESS(f"✔ Tenant {tenant.name} synchronized.")
                )
            except Exception as e:
                logger.exception(e)
                self.stdout.write(
                    self.style.ERROR(f"✘ Error synchronizing Tenant {tenant.name}: {e}")
                )

    def sync_gateways(self):
        self.stdout.write(self.style.NOTICE("Synchronizing Gateways..."))
        for gw in Gateway.objects.all():
            try:
                sync_gateway_get(gw)
                self.stdout.write(
                    self.style.SUCCESS(f"✔ Gateway {gw.name} synchronized.")
                )
            except Exception as e:
                logger.exception(e)
                self.stdout.write(
                    self.style.ERROR(f"✘ Error synchronizing Gateway {gw.name}: {e}")
                )

    def sync_api_users(self):
        self.stdout.write(self.style.NOTICE("Synchronizing APIUsers..."))
        for u in ApiUser.objects.all():
            try:
                sync_api_user_get(u)
                self.stdout.write(
                    self.style.SUCCESS(f"✔ APIUser {u.email} synchronized.")
                )
            except Exception as e:
                logger.exception(e)
                self.stdout.write(
                    self.style.ERROR(f"✘ Error synchronizing APIUser {u.email}: {e}")
                )

    def sync_applications(self):
        self.stdout.write(self.style.NOTICE("Synchronizing Applications..."))
        for app in Application.objects.all():
            try:
                sync_application_get(app)
                self.stdout.write(
                    self.style.SUCCESS(f"✔ Application {app.name} synchronized.")
                )
            except Exception as e:
                logger.exception(e)
                self.stdout.write(
                    self.style.ERROR(
                        f"✘ Error synchronizing Application {app.name}: {e}"
                    )
                )

    def sync_device_profiles(self):
        self.stdout.write(self.style.NOTICE("Synchronizing DeviceProfiles..."))
        for dp in DeviceProfile.objects.all():
            try:
                sync_device_profile_get(dp)
                self.stdout.write(
                    self.style.SUCCESS(f"✔ DeviceProfile {dp.name} synchronized.")
                )
            except Exception as e:
                logger.exception(e)
                self.stdout.write(
                    self.style.ERROR(
                        f"✘ Error synchronizing DeviceProfile {dp.name}: {e}"
                    )
                )

    def sync_devices(self):
        self.stdout.write(self.style.NOTICE("Synchronizing Devices..."))
        for device in Device.objects.all():
            try:
                sync_device_get(device)
                self.stdout.write(
                    self.style.SUCCESS(f"✔ Device {device.name} synchronized.")
                )
            except Exception as e:
                logger.exception(e)
                self.stdout.write(
                    self.style.ERROR(f"✘ Error synchronizing Device {device.name}: {e}")
                )
