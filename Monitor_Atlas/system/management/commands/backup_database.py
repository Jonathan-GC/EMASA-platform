import sys
from django.core.management.base import BaseCommand
from system.services.backup_service import BackupService


class Command(BaseCommand):
    help = "Trigger a manual database backup and stream to Cloudflare R2 storage."

    def add_arguments(self, parser):
        parser.add_argument(
            "--notes",
            type=str,
            default="",
            help="Optional operator notes describing the backup.",
        )

    def handle(self, *args, **options):
        notes = options.get("notes", "")
        self.stdout.write(self.style.NOTICE("Initiating database backup pipeline..."))

        service = BackupService()
        try:
            backup = service.create_backup(trigger_type="MANUAL_CLI", notes=notes)
            self.stdout.write(self.style.SUCCESS("Database backup completed successfully!"))
            self.stdout.write("=" * 60)
            self.stdout.write(f"Backup ID:          {backup.id}")
            self.stdout.write(f"Filename:           {backup.filename}")
            self.stdout.write(f"S3 Key:             {backup.s3_key}")
            self.stdout.write(f"Status:             {backup.status}")
            self.stdout.write(f"Size:               {backup.size_formatted} ({backup.size_bytes} bytes)")
            self.stdout.write(f"SHA-256 Checksum:   {backup.checksum_sha256}")
            self.stdout.write(f"Execution Duration: {backup.duration_seconds}s")
            if backup.notes:
                self.stdout.write(f"Notes:              {backup.notes}")
            self.stdout.write("=" * 60)
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f"Backup failed: {exc}"))
            sys.exit(1)
