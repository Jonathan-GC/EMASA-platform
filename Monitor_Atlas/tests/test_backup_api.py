from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from system.models import DatabaseBackup
from system.services.backup_service import BackupInProgressError

User = get_user_model()


class DatabaseBackupAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.superuser = User.objects.create_superuser(
            username="super_admin",
            email="superuser@example.com",
            password="password123",
        )
        self.regular_user = User.objects.create_user(
            username="regular_user",
            email="regular@example.com",
            password="password123",
        )

        self.list_url = "/api/v1/system/backups/"

    def test_unauthenticated_request_rejected(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_non_superuser_rejected_with_403(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.post(self.list_url, {"notes": "test"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_superuser_list_backups(self):
        self.client.force_authenticate(user=self.superuser)

        b1 = DatabaseBackup.objects.create(
            filename="backup1.sql.gz",
            s3_key="backups/backup1.sql.gz",
            status="COMPLETED",
            trigger_type="MANUAL_CLI",
            size_bytes=1048576,
        )
        b2 = DatabaseBackup.objects.create(
            filename="backup2.sql.gz",
            s3_key="backups/backup2.sql.gz",
            status="FAILED",
            trigger_type="MANUAL_API",
            size_bytes=0,
        )

        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn("results", data)
        self.assertEqual(data["count"], 2)

        # Filtering by status
        response_filtered = self.client.get(self.list_url, {"status": "COMPLETED"})
        self.assertEqual(response_filtered.status_code, status.HTTP_200_OK)
        filtered_data = response_filtered.json()
        self.assertEqual(filtered_data["count"], 1)
        self.assertEqual(filtered_data["results"][0]["id"], b1.id)

        # Filtering by trigger_type
        response_trigger = self.client.get(self.list_url, {"trigger_type": "MANUAL_API"})
        self.assertEqual(response_trigger.status_code, status.HTTP_200_OK)
        trigger_data = response_trigger.json()
        self.assertEqual(trigger_data["count"], 1)
        self.assertEqual(trigger_data["results"][0]["id"], b2.id)

    def test_retrieve_backup_detail(self):
        self.client.force_authenticate(user=self.superuser)

        now = timezone.now()
        backup = DatabaseBackup.objects.create(
            filename="detail_test.sql.gz",
            s3_key="backups/postgresql/2026/10/detail_test.sql.gz",
            status="COMPLETED",
            size_bytes=10485760,
            checksum_sha256="c" * 64,
            trigger_type="MANUAL_API",
            triggered_by=self.superuser,
            notes="Snapshot pre-migration",
            started_at=now,
            completed_at=now + timezone.timedelta(seconds=45),
        )

        detail_url = f"/api/v1/system/backups/{backup.id}/"
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertEqual(data["id"], backup.id)
        self.assertEqual(data["filename"], "detail_test.sql.gz")
        self.assertEqual(data["s3_key"], "backups/postgresql/2026/10/detail_test.sql.gz")
        self.assertEqual(data["size_formatted"], "10.0 MB")
        self.assertEqual(data["duration_seconds"], 45.0)
        self.assertEqual(data["checksum_sha256"], "c" * 64)
        self.assertEqual(data["notes"], "Snapshot pre-migration")
        self.assertIsNotNone(data["triggered_by"])
        self.assertEqual(data["triggered_by"]["username"], "super_admin")

    def test_retrieve_nonexistent_backup_returns_404(self):
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get("/api/v1/system/backups/nonexistent12345/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch("system.views.BackupService")
    def test_trigger_backup_success(self, mock_service_cls):
        self.client.force_authenticate(user=self.superuser)
        mock_service = MagicMock()
        mock_service_cls.return_value = mock_service

        created_backup = DatabaseBackup(
            id="newbackup1234567",
            filename="backup_new.sql.gz",
            s3_key="backups/backup_new.sql.gz",
            status="COMPLETED",
            trigger_type="MANUAL_API",
            triggered_by=self.superuser,
            notes="Manual trigger via API",
            size_bytes=2048,
            checksum_sha256="d" * 64,
        )
        mock_service.create_backup.return_value = created_backup

        payload = {"notes": "Manual trigger via API"}
        response = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertEqual(data["id"], "newbackup1234567")
        self.assertEqual(data["notes"], "Manual trigger via API")
        mock_service.create_backup.assert_called_once_with(
            trigger_type="MANUAL_API",
            user=self.superuser,
            notes="Manual trigger via API",
        )

    @patch("system.views.BackupService")
    def test_trigger_backup_conflict_returns_409(self, mock_service_cls):
        self.client.force_authenticate(user=self.superuser)
        mock_service = MagicMock()
        mock_service_cls.return_value = mock_service
        mock_service.create_backup.side_effect = BackupInProgressError("A backup is currently in progress.")

        response = self.client.post(self.list_url, {"notes": "overlapping"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertIn("already in progress", response.json()["detail"])

    @patch("system.views.BackupService")
    def test_generate_download_url_success(self, mock_service_cls):
        self.client.force_authenticate(user=self.superuser)
        mock_service = MagicMock()
        mock_service_cls.return_value = mock_service
        mock_service.generate_presigned_download_url.return_value = (
            "https://r2.storage/download?signature=secure"
        )

        backup = DatabaseBackup.objects.create(
            filename="download_ready.sql.gz",
            s3_key="backups/download_ready.sql.gz",
            status="COMPLETED",
            size_bytes=4096,
            checksum_sha256="e" * 64,
        )

        url = f"/api/v1/system/backups/{backup.id}/download_url/"
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["download_url"], "https://r2.storage/download?signature=secure")
        self.assertEqual(data["expires_in"], 900)
        self.assertEqual(data["filename"], "download_ready.sql.gz")
        self.assertEqual(data["size_bytes"], 4096)
        self.assertEqual(data["checksum_sha256"], "e" * 64)

    def test_generate_download_url_non_completed_returns_400(self):
        self.client.force_authenticate(user=self.superuser)
        backup = DatabaseBackup.objects.create(
            filename="failed.sql.gz",
            s3_key="backups/failed.sql.gz",
            status="FAILED",
        )

        url = f"/api/v1/system/backups/{backup.id}/download_url/"
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("not in completed state", response.json()["detail"])

    @patch("system.views.BackupService")
    def test_delete_backup_success(self, mock_service_cls):
        self.client.force_authenticate(user=self.superuser)
        mock_service = MagicMock()
        mock_service_cls.return_value = mock_service

        backup = DatabaseBackup.objects.create(
            filename="to_delete.sql.gz",
            s3_key="backups/to_delete.sql.gz",
            status="COMPLETED",
        )

        url = f"/api/v1/system/backups/{backup.id}/"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        mock_service.delete_backup.assert_called_once_with(backup, actor=self.superuser)

    def test_delete_in_progress_backup_returns_409(self):
        self.client.force_authenticate(user=self.superuser)
        backup = DatabaseBackup.objects.create(
            filename="running.sql.gz",
            s3_key="backups/running.sql.gz",
            status="IN_PROGRESS",
        )

        url = f"/api/v1/system/backups/{backup.id}/"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertIn("Cannot delete a backup currently in progress", response.json()["detail"])

    def test_restore_prohibited_via_api_returns_405(self):
        self.client.force_authenticate(user=self.superuser)
        backup = DatabaseBackup.objects.create(
            filename="restore_blocked.sql.gz",
            s3_key="backups/restore_blocked.sql.gz",
            status="COMPLETED",
        )

        url = f"/api/v1/system/backups/{backup.id}/restore/"
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertIn("Database restoration via REST API is strictly forbidden", response.json()["detail"])
