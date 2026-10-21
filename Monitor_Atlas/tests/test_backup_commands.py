import io
from unittest.mock import MagicMock, patch

from django.core.management import call_command
from django.test import TestCase

from system.models import DatabaseBackup
from system.services.backup_service import (
    IntegrityVerificationError,
    BackupExecutionError,
)


class BackupCommandsTests(TestCase):
    @patch("system.management.commands.backup_database.BackupService")
    def test_backup_database_command_success(self, mock_service_cls):
        mock_service = MagicMock()
        mock_service_cls.return_value = mock_service

        mock_backup = DatabaseBackup(
            id="abc123def4567890",
            filename="backup_20261005_120000.sql.gz",
            s3_key="backups/postgresql/2026/10/backup_20261005_120000.sql.gz",
            status="COMPLETED",
            size_bytes=1048576,
            checksum_sha256="f" * 64,
            notes="Weekly automated backup",
        )
        mock_service.create_backup.return_value = mock_backup

        out = io.StringIO()
        err = io.StringIO()
        call_command("backup_database", "--notes", "Weekly automated backup", stdout=out, stderr=err)

        output = out.getvalue()
        self.assertIn("Database backup completed successfully!", output)
        self.assertIn("abc123def4567890", output)
        self.assertIn("Weekly automated backup", output)
        self.assertIn("1.0 MB", output)
        mock_service.create_backup.assert_called_once_with(
            trigger_type="MANUAL_CLI",
            notes="Weekly automated backup",
        )

    @patch("system.management.commands.backup_database.BackupService")
    def test_backup_database_command_failure_exits_1(self, mock_service_cls):
        mock_service = MagicMock()
        mock_service_cls.return_value = mock_service
        mock_service.create_backup.side_effect = BackupExecutionError("pg_dump process terminated")

        out = io.StringIO()
        err = io.StringIO()
        with self.assertRaises(SystemExit) as cm:
            call_command("backup_database", stdout=out, stderr=err)

        self.assertEqual(cm.exception.code, 1)
        self.assertIn("Backup failed: pg_dump process terminated", err.getvalue())

    def test_restore_database_command_without_confirm_aborts(self):
        out = io.StringIO()
        err = io.StringIO()

        with patch("sys.stdin.isatty", return_value=False):
            with self.assertRaises(SystemExit) as cm:
                call_command("restore_database", "test_backup_id", stdout=out, stderr=err)

        self.assertEqual(cm.exception.code, 1)
        self.assertIn("Restoration requires explicit confirmation. Please pass --confirm flag.", err.getvalue())

    @patch("system.management.commands.restore_database.BackupService")
    def test_restore_database_command_success(self, mock_service_cls):
        mock_service = MagicMock()
        mock_service_cls.return_value = mock_service
        mock_service.restore_database.return_value = {
            "status": "SUCCESS",
            "duration_seconds": 12.34,
            "size_bytes": 5242880,
            "checksum_sha256": "e" * 64,
        }

        out = io.StringIO()
        err = io.StringIO()
        call_command("restore_database", "valid_backup_id", "--confirm", stdout=out, stderr=err)

        output = out.getvalue()
        self.assertIn("Database restored successfully!", output)
        self.assertIn("5242880 bytes", output)
        self.assertIn("12.34s", output)
        mock_service.restore_database.assert_called_once_with(
            backup_id_or_file="valid_backup_id",
            confirm=True,
        )

    @patch("system.management.commands.restore_database.BackupService")
    def test_restore_database_command_integrity_error_exits_1(self, mock_service_cls):
        mock_service = MagicMock()
        mock_service_cls.return_value = mock_service
        mock_service.restore_database.side_effect = IntegrityVerificationError(
            "SHA-256 checksum mismatch: archive may be corrupted or altered."
        )

        out = io.StringIO()
        err = io.StringIO()
        with self.assertRaises(SystemExit) as cm:
            call_command("restore_database", "corrupted_id", "--confirm", stdout=out, stderr=err)

        self.assertEqual(cm.exception.code, 1)
        self.assertIn("Integrity check failed", err.getvalue())
