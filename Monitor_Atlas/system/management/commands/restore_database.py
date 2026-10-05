import sys
from django.core.management.base import BaseCommand
from system.services.backup_service import (
    BackupService,
    IntegrityVerificationError,
    RestoreExecutionError,
)


class Command(BaseCommand):
    help = "Restore PostgreSQL database from a Cloudflare R2 backup archive or local file."

    def add_arguments(self, parser):
        parser.add_argument(
            "backup_id_or_file",
            type=str,
            help="16-character DatabaseBackup ID, UUID, or local path to .sql.gz archive.",
        )
        parser.add_argument(
            "--confirm",
            action="store_true",
            help="Explicit confirmation required to execute destructive database replacement.",
        )

    def handle(self, *args, **options):
        backup_id_or_file = options["backup_id_or_file"]
        confirm = options.get("confirm", False)

        if not confirm:
            self.stderr.write(
                self.style.WARNING(
                    "WARNING: Database restoration will overwrite and replace the active database!"
                )
            )
            if sys.stdin.isatty():
                try:
                    confirmation = input("Type 'RESTORE' to confirm: ")
                except (EOFError, KeyboardInterrupt):
                    self.stderr.write(self.style.ERROR("\nRestoration aborted."))
                    sys.exit(1)

                if confirmation.strip() != "RESTORE":
                    self.stderr.write(self.style.ERROR("Restoration aborted by operator."))
                    sys.exit(1)
            else:
                self.stderr.write(
                    self.style.ERROR(
                        "Restoration requires explicit confirmation. Please pass --confirm flag."
                    )
                )
                sys.exit(1)

        self.stdout.write(self.style.NOTICE(f"Initiating restoration from: {backup_id_or_file}"))
        self.stdout.write("Downloading archive and verifying SHA-256 integrity...")

        service = BackupService()
        try:
            summary = service.restore_database(backup_id_or_file=backup_id_or_file, confirm=True)
            self.stdout.write(self.style.SUCCESS("Database restored successfully!"))
            self.stdout.write("=" * 60)
            self.stdout.write(f"Status:             {summary.get('status')}")
            self.stdout.write(f"Archive Size:       {summary.get('size_bytes')} bytes")
            self.stdout.write(f"SHA-256 Checksum:   {summary.get('checksum_sha256')}")
            self.stdout.write(f"Execution Duration: {summary.get('duration_seconds')}s")
            self.stdout.write("=" * 60)
        except IntegrityVerificationError as exc:
            self.stderr.write(self.style.ERROR(f"Integrity check failed: {exc}"))
            sys.exit(1)
        except RestoreExecutionError as exc:
            self.stderr.write(self.style.ERROR(f"Restoration failed: {exc}"))
            sys.exit(1)
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f"Unexpected restoration error: {exc}"))
            sys.exit(1)
