import gzip
import hashlib
import io
import os
import tempfile
from datetime import timedelta
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone

from system.models import DatabaseBackup
from system.services.backup_service import (
    BackupService,
    BackupInProgressError,
    BackupExecutionError,
    RestoreExecutionError,
    IntegrityVerificationError,
    GzipHashingStream,
)

User = get_user_model()


class BackupServiceTests(TestCase):
    def setUp(self):
        self.service = BackupService()
        self.user = User.objects.create_user(
            username="backup_admin",
            email="admin@example.com",
            password="password123",
        )

    def test_gzip_hashing_stream_compression_and_digest(self):
        content = b"INSERT INTO table VALUES (1, 'test', 'data');" * 100
        source = io.BytesIO(content)
        stream = GzipHashingStream(source)

        compressed_data = bytearray()
        while True:
            chunk = stream.read(128)
            if not chunk:
                break
            compressed_data.extend(chunk)

        self.assertEqual(stream.total_bytes, len(compressed_data))
        self.assertEqual(stream.hasher.hexdigest(), hashlib.sha256(compressed_data).hexdigest())

        decompressed = gzip.decompress(bytes(compressed_data))
        self.assertEqual(decompressed, content)

    @override_settings(
        R2_ACCESS_KEY_ID="test_access",
        R2_SECRET_ACCESS_KEY="test_secret",
        R2_ENDPOINT_URL="https://test.r2.cloudflarestorage.com",
        R2_REGION_NAME="auto",
        R2_BUCKET_NAME="test-backups",
    )
    @patch("system.services.backup_service.boto3.client")
    def test_r2_client_initialization(self, mock_boto_client):
        self.service._get_r2_client()
        mock_boto_client.assert_called_once_with(
            "s3",
            endpoint_url="https://test.r2.cloudflarestorage.com",
            aws_access_key_id="test_access",
            aws_secret_access_key="test_secret",
            region_name="auto",
        )
        self.assertEqual(self.service.bucket_name, "test-backups")

    def test_acquire_concurrency_lock_success(self):
        self.assertEqual(DatabaseBackup.objects.filter(status="IN_PROGRESS").count(), 0)
        # Should not raise
        self.service.acquire_concurrency_lock()

    def test_acquire_concurrency_lock_rejection_when_running(self):
        DatabaseBackup.objects.create(
            filename="active.sql.gz",
            s3_key="backups/active.sql.gz",
            status="IN_PROGRESS",
            started_at=timezone.now(),
        )
        with self.assertRaises(BackupInProgressError):
            self.service.acquire_concurrency_lock()

    def test_acquire_concurrency_lock_recovers_stale_lock(self):
        stale_time = timezone.now() - timedelta(hours=3)
        stale_backup = DatabaseBackup.objects.create(
            filename="stale.sql.gz",
            s3_key="backups/stale.sql.gz",
            status="IN_PROGRESS",
            started_at=stale_time,
        )

        # Should recover stale lock and acquire
        self.service.acquire_concurrency_lock()

        stale_backup.refresh_from_db()
        self.assertEqual(stale_backup.status, "FAILED")
        self.assertIn("exceeded 2-hour timeout", stale_backup.error_message)
        self.assertIsNotNone(stale_backup.completed_at)

    @override_settings(USE_R2=True)
    @patch("system.services.backup_service.subprocess.Popen")
    @patch.object(BackupService, "_get_r2_client")
    def test_create_backup_success(self, mock_get_client, mock_popen):
        mock_client = MagicMock()
        def fake_upload(stream, bucket, key):
            while stream.read(4096):
                pass
        mock_client.upload_fileobj.side_effect = fake_upload
        mock_get_client.return_value = mock_client

        raw_sql = b"SELECT 1;\n" * 50
        mock_proc = MagicMock()
        mock_proc.stdout = io.BytesIO(raw_sql)
        mock_proc.wait.return_value = 0
        mock_popen.return_value = mock_proc

        backup = self.service.create_backup(
            trigger_type="MANUAL_CLI",
            user=self.user,
            notes="Initial unit test backup",
        )

        self.assertIsNotNone(backup.id)
        self.assertEqual(backup.status, "COMPLETED")
        self.assertEqual(backup.trigger_type, "MANUAL_CLI")
        self.assertEqual(backup.triggered_by, self.user)
        self.assertEqual(backup.notes, "Initial unit test backup")
        self.assertTrue(backup.size_bytes > 0)
        self.assertEqual(len(backup.checksum_sha256), 64)
        self.assertIsNotNone(backup.started_at)
        self.assertIsNotNone(backup.completed_at)
        self.assertIsNotNone(backup.duration_seconds)
        self.assertTrue(backup.size_formatted.endswith("B"))

        mock_client.upload_fileobj.assert_called_once()
        uploaded_stream = mock_client.upload_fileobj.call_args[0][0]
        self.assertIsInstance(uploaded_stream, GzipHashingStream)

    @override_settings(USE_R2=True)
    @patch("system.services.backup_service.subprocess.Popen")
    @patch.object(BackupService, "_get_r2_client")
    def test_create_backup_failure_teardown(self, mock_get_client, mock_popen):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_proc = MagicMock()
        mock_proc.stdout = io.BytesIO(b"")
        mock_proc.wait.return_value = 1
        mock_proc.stderr.read.return_value = b"pg_dump: connection error to server"
        mock_proc.poll.return_value = 1
        mock_popen.return_value = mock_proc

        with self.assertRaises(BackupExecutionError):
            self.service.create_backup(trigger_type="MANUAL_CLI")

        failed_backup = DatabaseBackup.objects.first()
        self.assertIsNotNone(failed_backup)
        self.assertEqual(failed_backup.status, "FAILED")
        self.assertIn("connection error to server", failed_backup.error_message)
        mock_client.delete_object.assert_called_once()

    @override_settings(USE_R2=True)
    @patch.object(BackupService, "_get_r2_client")
    def test_generate_presigned_download_url_success(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.generate_presigned_url.return_value = "https://r2.storage/download?signed=1"
        mock_get_client.return_value = mock_client

        backup = DatabaseBackup.objects.create(
            filename="completed.sql.gz",
            s3_key="backups/postgresql/2026/10/completed.sql.gz",
            status="COMPLETED",
            size_bytes=1024,
            checksum_sha256="a" * 64,
        )

        url = self.service.generate_presigned_download_url(backup, expires_in=900)
        self.assertEqual(url, "https://r2.storage/download?signed=1")
        mock_client.generate_presigned_url.assert_called_once_with(
            "get_object",
            Params={"Bucket": self.service.bucket_name, "Key": backup.s3_key},
            ExpiresIn=900,
        )

    def test_generate_presigned_download_url_non_completed_rejected(self):
        failed_backup = DatabaseBackup.objects.create(
            filename="failed.sql.gz",
            s3_key="backups/failed.sql.gz",
            status="FAILED",
        )
        with self.assertRaises(ValueError):
            self.service.generate_presigned_download_url(failed_backup)

    @override_settings(USE_R2=True)
    @patch.object(BackupService, "_get_r2_client")
    def test_delete_backup_success(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        backup = DatabaseBackup.objects.create(
            filename="to_delete.sql.gz",
            s3_key="backups/to_delete.sql.gz",
            status="COMPLETED",
        )
        backup_id = backup.id

        self.service.delete_backup(backup)
        mock_client.delete_object.assert_called_once_with(
            Bucket=self.service.bucket_name,
            Key="backups/to_delete.sql.gz",
        )
        self.assertFalse(DatabaseBackup.objects.filter(id=backup_id).exists())

    def test_delete_backup_in_progress_rejected(self):
        backup = DatabaseBackup.objects.create(
            filename="running.sql.gz",
            s3_key="backups/running.sql.gz",
            status="IN_PROGRESS",
        )
        with self.assertRaises(BackupInProgressError):
            self.service.delete_backup(backup)
        self.assertTrue(DatabaseBackup.objects.filter(id=backup.id).exists())

    def test_restore_database_requires_confirmation(self):
        with self.assertRaises(ValueError):
            self.service.restore_database("dummy_id", confirm=False)

    @patch.object(BackupService, "_get_r2_client")
    def test_restore_database_checksum_mismatch(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        def fake_download(bucket, key, filename):
            with open(filename, "wb") as f:
                f.write(b"corrupted archive data")

        mock_client.download_file.side_effect = fake_download

        backup = DatabaseBackup.objects.create(
            filename="test.sql.gz",
            s3_key="backups/test.sql.gz",
            status="COMPLETED",
            checksum_sha256="expected_sha256_which_will_not_match",
        )

        with self.assertRaises(IntegrityVerificationError):
            self.service.restore_database(backup.id, confirm=True)

    @patch("system.services.backup_service.subprocess.Popen")
    @patch.object(BackupService, "_get_r2_client")
    def test_restore_database_success(self, mock_get_client, mock_popen):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        raw_sql = b"DROP TABLE IF EXISTS test; CREATE TABLE test (id int);"
        compressed = gzip.compress(raw_sql)
        expected_sha256 = hashlib.sha256(compressed).hexdigest()

        def fake_download(bucket, key, filename):
            with open(filename, "wb") as f:
                f.write(compressed)

        mock_client.download_file.side_effect = fake_download

        mock_proc = MagicMock()
        mock_proc.communicate.return_value = (b"", b"")
        mock_proc.returncode = 0
        mock_popen.return_value = mock_proc

        backup = DatabaseBackup.objects.create(
            filename="restore_test.sql.gz",
            s3_key="backups/restore_test.sql.gz",
            status="COMPLETED",
            size_bytes=len(compressed),
            checksum_sha256=expected_sha256,
        )

        result = self.service.restore_database(backup.id, confirm=True)
        self.assertEqual(result["status"], "SUCCESS")
        self.assertEqual(result["checksum_sha256"], expected_sha256)
        self.assertEqual(result["size_bytes"], len(compressed))
        self.assertIn("duration_seconds", result)

    @override_settings(
        USE_R2=True,
        R2_ACCESS_KEY_ID="test_key",
        R2_SECRET_ACCESS_KEY="test_secret",
        R2_ENDPOINT_URL="https://account.r2.cloudflarestorage.com",
        R2_BUCKET_NAME="test-bucket",
    )
    def test_is_r2_configured_returns_true_when_configured(self):
        self.assertTrue(self.service.is_r2_configured())

    @override_settings(
        USE_R2=False,
        R2_ACCESS_KEY_ID="test_key",
        R2_SECRET_ACCESS_KEY="test_secret",
        R2_ENDPOINT_URL="https://account.r2.cloudflarestorage.com",
        R2_BUCKET_NAME="test-bucket",
    )
    def test_is_r2_configured_returns_false_when_use_r2_is_false(self):
        self.assertFalse(self.service.is_r2_configured())

    @override_settings(
        R2_ACCESS_KEY_ID=None,
        R2_SECRET_ACCESS_KEY="test_secret",
        R2_ENDPOINT_URL="https://account.r2.cloudflarestorage.com",
        R2_BUCKET_NAME="test-bucket",
    )
    def test_is_r2_configured_returns_false_when_none(self):
        self.assertFalse(self.service.is_r2_configured())

    @override_settings(
        R2_ACCESS_KEY_ID="",
        R2_SECRET_ACCESS_KEY="test_secret",
        R2_ENDPOINT_URL="https://account.r2.cloudflarestorage.com",
        R2_BUCKET_NAME="test-bucket",
    )
    def test_is_r2_configured_returns_false_when_empty_string(self):
        self.assertFalse(self.service.is_r2_configured())

    @override_settings(
        R2_ACCESS_KEY_ID="   ",
        R2_SECRET_ACCESS_KEY="test_secret",
        R2_ENDPOINT_URL="https://account.r2.cloudflarestorage.com",
        R2_BUCKET_NAME="test-bucket",
    )
    def test_is_r2_configured_returns_false_when_whitespace_only(self):
        self.assertFalse(self.service.is_r2_configured())

    @patch("system.services.backup_service.subprocess.Popen")
    def test_create_backup_fallback_to_local_file_when_r2_unconfigured(self, mock_popen):
        with tempfile.TemporaryDirectory() as temp_dir:
            with override_settings(
                R2_ACCESS_KEY_ID=None,
                R2_SECRET_ACCESS_KEY=None,
                R2_ENDPOINT_URL=None,
                R2_BUCKET_NAME=None,
                BACKUP_LOCAL_DIR=temp_dir,
            ):
                raw_sql = b"SELECT 1;\n" * 50
                mock_proc = MagicMock()
                mock_proc.stdout = io.BytesIO(raw_sql)
                mock_proc.wait.return_value = 0
                mock_popen.return_value = mock_proc

                backup = self.service.create_backup(
                    trigger_type="MANUAL_CLI",
                    user=self.user,
                    notes="Local fallback unit test",
                )

                self.assertEqual(backup.status, "COMPLETED")
                local_path = self.service.get_local_path(backup.s3_key)
                self.assertTrue(os.path.exists(local_path))

                with open(local_path, "rb") as f:
                    compressed_bytes = f.read()
                decompressed = gzip.decompress(compressed_bytes)
                self.assertEqual(decompressed, raw_sql)
                self.assertEqual(backup.checksum_sha256, hashlib.sha256(compressed_bytes).hexdigest())
                self.assertEqual(backup.size_bytes, len(compressed_bytes))

    @patch("system.services.backup_service.subprocess.Popen")
    def test_create_backup_local_failure_cleans_up_partial_file(self, mock_popen):
        with tempfile.TemporaryDirectory() as temp_dir:
            with override_settings(
                R2_ACCESS_KEY_ID=None,
                R2_SECRET_ACCESS_KEY=None,
                R2_ENDPOINT_URL=None,
                R2_BUCKET_NAME=None,
                BACKUP_LOCAL_DIR=temp_dir,
            ):
                mock_proc = MagicMock()
                mock_proc.stdout = io.BytesIO(b"PARTIAL DUMP DATA")
                mock_proc.wait.return_value = 1
                mock_proc.stderr.read.return_value = b"pg_dump: disk full or query failed"
                mock_proc.poll.return_value = 1
                mock_popen.return_value = mock_proc

                with self.assertRaises(BackupExecutionError):
                    self.service.create_backup(trigger_type="MANUAL_CLI")

                failed_backup = DatabaseBackup.objects.first()
                self.assertIsNotNone(failed_backup)
                self.assertEqual(failed_backup.status, "FAILED")
                self.assertIn("disk full or query failed", failed_backup.error_message)

                local_path = self.service.get_local_path(failed_backup.s3_key)
                self.assertFalse(os.path.exists(local_path))

    @patch("system.services.backup_service.subprocess.Popen")
    def test_restore_database_using_local_file_when_r2_unconfigured(self, mock_popen):
        with tempfile.TemporaryDirectory() as temp_dir:
            with override_settings(
                R2_ACCESS_KEY_ID=None,
                R2_SECRET_ACCESS_KEY=None,
                R2_ENDPOINT_URL=None,
                R2_BUCKET_NAME=None,
                BACKUP_LOCAL_DIR=temp_dir,
            ):
                raw_sql = b"DROP TABLE IF EXISTS test_tbl; CREATE TABLE test_tbl (id int);"
                compressed = gzip.compress(raw_sql)
                expected_sha256 = hashlib.sha256(compressed).hexdigest()

                local_path = self.service.get_local_path("backups/postgresql/2026/10/local_restore.sql.gz")
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                with open(local_path, "wb") as f:
                    f.write(compressed)

                mock_proc = MagicMock()
                mock_proc.communicate.return_value = (b"", b"")
                mock_proc.returncode = 0
                mock_popen.return_value = mock_proc

                backup = DatabaseBackup.objects.create(
                    filename="local_restore.sql.gz",
                    s3_key="backups/postgresql/2026/10/local_restore.sql.gz",
                    status="COMPLETED",
                    size_bytes=len(compressed),
                    checksum_sha256=expected_sha256,
                )

                result = self.service.restore_database(backup.id, confirm=True)
                self.assertEqual(result["status"], "SUCCESS")
                self.assertEqual(result["checksum_sha256"], expected_sha256)
                self.assertEqual(result["size_bytes"], len(compressed))
                # Persistent local file should not be deleted upon successful restore
                self.assertTrue(os.path.exists(local_path))

    def test_delete_backup_deletes_local_file_when_present(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with override_settings(
                R2_ACCESS_KEY_ID=None,
                R2_SECRET_ACCESS_KEY=None,
                R2_ENDPOINT_URL=None,
                R2_BUCKET_NAME=None,
                BACKUP_LOCAL_DIR=temp_dir,
            ):
                local_path = self.service.get_local_path("backups/to_del.sql.gz")
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                with open(local_path, "wb") as f:
                    f.write(b"backup payload")

                backup = DatabaseBackup.objects.create(
                    filename="to_del.sql.gz",
                    s3_key="backups/to_del.sql.gz",
                    status="COMPLETED",
                )
                backup_id = backup.id

                self.assertTrue(os.path.exists(local_path))
                self.service.delete_backup(backup)
                self.assertFalse(os.path.exists(local_path))
                self.assertFalse(DatabaseBackup.objects.filter(id=backup_id).exists())

    @override_settings(
        R2_ACCESS_KEY_ID=None,
        R2_SECRET_ACCESS_KEY=None,
        R2_ENDPOINT_URL=None,
        R2_BUCKET_NAME=None,
    )
    def test_generate_presigned_download_url_returns_local_path_when_r2_unconfigured(self):
        backup = DatabaseBackup.objects.create(
            filename="local_dl.sql.gz",
            s3_key="backups/local_dl.sql.gz",
            status="COMPLETED",
        )
        url = self.service.generate_presigned_download_url(backup)
        self.assertEqual(url, f"/api/v1/system/backups/{backup.id}/download/")

