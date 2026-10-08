import gzip
import hashlib
import io
import os
import subprocess
import tempfile
import zlib
from datetime import timedelta
from typing import Any, Optional

import boto3
from botocore.exceptions import ClientError
from django.conf import settings
from django.db import connection, transaction
from django.utils import timezone
from loguru import logger

from system.models import DatabaseBackup


class BackupInProgressError(Exception):
    """Raised when a backup operation is attempted while another is already running."""


class BackupExecutionError(Exception):
    """Raised when pg_dump or the streaming upload pipeline fails."""


class RestoreExecutionError(Exception):
    """Raised when database restoration fails during execution."""


class IntegrityVerificationError(Exception):
    """Raised when archive checksum does not match expected value."""


# Alias for compatibility with callers expecting ChecksumMismatchError
ChecksumMismatchError = IntegrityVerificationError


class GzipHashingStream(io.RawIOBase):
    """
    Pipes an uncompressed input stream through gzip compression on-the-fly,
    computing the SHA-256 hash digest and tracking total compressed bytes
    as chunks are consumed by upload_fileobj.
    """

    def __init__(self, source_stream: Any):
        self.source_stream = source_stream
        # wbits=31 produces standard gzip header and trailer (16 + MAX_WBITS)
        self.compressor = zlib.compressobj(
            level=9,
            method=zlib.DEFLATED,
            wbits=31,
        )
        self.hasher = hashlib.sha256()
        self.buffer = bytearray()
        self.total_bytes = 0
        self.eof = False

    def readable(self) -> bool:
        return True

    def read(self, size: int = -1) -> bytes:
        if size is None or size < 0:
            while not self.eof:
                chunk = self.source_stream.read(65536)
                if not chunk:
                    self.eof = True
                    compressed = self.compressor.flush()
                else:
                    compressed = self.compressor.compress(chunk)
                if compressed:
                    self.hasher.update(compressed)
                    self.total_bytes += len(compressed)
                    self.buffer.extend(compressed)
            res = bytes(self.buffer)
            self.buffer.clear()
            return res

        while len(self.buffer) < size and not self.eof:
            chunk = self.source_stream.read(65536)
            if not chunk:
                self.eof = True
                compressed = self.compressor.flush()
            else:
                compressed = self.compressor.compress(chunk)
            if compressed:
                self.hasher.update(compressed)
                self.total_bytes += len(compressed)
                self.buffer.extend(compressed)

        if not self.buffer and self.eof:
            return b""

        bytes_to_return = bytes(self.buffer[:size])
        del self.buffer[:size]
        return bytes_to_return

    def readinto(self, b: bytearray) -> int:
        data = self.read(len(b))
        n = len(data)
        b[:n] = data
        return n


class BackupService:
    """
    Manages database backup creation, Cloudflare R2 storage streaming,
    concurrency locking, pre-signed URL generation, and verified restorations.
    """

    def __init__(self):
        pass

    def _get_r2_client(self):
        """Initializes and returns a boto3 S3 client configured for Cloudflare R2."""
        endpoint_url = getattr(settings, "R2_ENDPOINT_URL", None)
        aws_access_key_id = getattr(settings, "R2_ACCESS_KEY_ID", None)
        aws_secret_access_key = getattr(settings, "R2_SECRET_ACCESS_KEY", None)
        region_name = getattr(settings, "R2_REGION_NAME", "auto")

        return boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name,
        )

    def get_r2_client(self):
        return self._get_r2_client()

    @property
    def bucket_name(self) -> str:
        return getattr(settings, "R2_BUCKET_NAME", "emasa-backups") or "emasa-backups"

    def is_r2_configured(self) -> bool:
        """
        Checks that settings.R2_ACCESS_KEY_ID, settings.R2_SECRET_ACCESS_KEY,
        settings.R2_ENDPOINT_URL, and settings.R2_BUCKET_NAME are all configured,
        truthy, non-empty strings.
        """
        required_keys = [
            "R2_ACCESS_KEY_ID",
            "R2_SECRET_ACCESS_KEY",
            "R2_ENDPOINT_URL",
            "R2_BUCKET_NAME",
        ]
        for key in required_keys:
            val = getattr(settings, key, None)
            if not val or not isinstance(val, str) or not val.strip():
                return False
        return True

    def get_local_path(self, key_or_backup: Any) -> str:
        """
        Resolves the local absolute path for a backup key or DatabaseBackup instance.
        Uses BACKUP_LOCAL_DIR if defined, falling back to BASE_DIR.
        """
        if hasattr(key_or_backup, "s3_key"):
            s3_key = key_or_backup.s3_key
        else:
            s3_key = str(key_or_backup)
        base_dir = getattr(settings, "BACKUP_LOCAL_DIR", None) or settings.BASE_DIR
        clean_key = s3_key.lstrip("/\\")
        return os.path.join(str(base_dir), clean_key)

    def acquire_concurrency_lock(self) -> None:
        """
        Ensures no concurrent backup is executing. Stale in-progress records older
        than 2 hours are marked as FAILED to prevent permanent deadlock.
        """
        now = timezone.now()
        stale_threshold = now - timedelta(hours=2)

        with transaction.atomic():
            in_progress_backups = DatabaseBackup.objects.select_for_update().filter(status="IN_PROGRESS")
            for backup in in_progress_backups:
                if backup.started_at and backup.started_at < stale_threshold:
                    logger.warning(
                        f"Recovering stale backup lock for backup {backup.id} started at {backup.started_at}"
                    )
                    backup.status = "FAILED"
                    backup.error_message = "Backup execution exceeded 2-hour timeout (stale lock recovered)"
                    backup.completed_at = now
                    backup.save(update_fields=["status", "error_message", "completed_at", "updated_at"])
                else:
                    raise BackupInProgressError("A database backup is currently in progress.")

    def release_concurrency_lock(
        self,
        backup: DatabaseBackup,
        new_status: str,
        error_message: str = "",
    ) -> None:
        """Safely transitions backup status and marks completed_at timestamp."""
        backup.status = new_status
        backup.completed_at = timezone.now()
        if error_message:
            backup.error_message = error_message
        backup.save(update_fields=["status", "completed_at", "error_message", "updated_at"])

    def create_backup(
        self,
        trigger_type: str = "MANUAL_CLI",
        user: Any = None,
        triggered_by: Any = None,
        notes: str = "",
    ) -> DatabaseBackup:
        """
        Executes streaming pg_dump, in-flight gzip compression and SHA-256 calculation,
        and streams directly to Cloudflare R2 without local uncompressed disk storage.
        """
        actor = triggered_by if triggered_by is not None else user
        self.acquire_concurrency_lock()

        now = timezone.now()
        timestamp_str = now.strftime("%Y%m%d_%H%M%S")
        filename = f"backup_{timestamp_str}.sql.gz"
        s3_key = f"backups/postgresql/{now.strftime('%Y/%m')}/{filename}"

        backup = DatabaseBackup.objects.create(
            filename=filename,
            s3_key=s3_key,
            status="IN_PROGRESS",
            trigger_type=trigger_type,
            triggered_by=actor,
            notes=notes,
            started_at=now,
        )

        db_config = settings.DATABASES.get("default", {})
        host = db_config.get("HOST") or "127.0.0.1"
        port = str(db_config.get("PORT") or "5432")
        db_user = db_config.get("USER") or "postgres"
        db_password = db_config.get("PASSWORD") or ""
        dbname = db_config.get("NAME") or "atlas"

        env = os.environ.copy()
        if db_password:
            env["PGPASSWORD"] = db_password

        cmd = [
            "pg_dump",
            "-h", host,
            "-p", port,
            "-U", db_user,
            "-d", dbname,
            "--clean",
            "--if-exists",
            "--no-owner",
            "--no-privileges",
        ]

        proc = None
        local_dest = None
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
            )

            stream = GzipHashingStream(proc.stdout)
            if self.is_r2_configured():
                client = self._get_r2_client()
                client.upload_fileobj(stream, self.bucket_name, s3_key)
            else:
                local_dest = self.get_local_path(s3_key)
                os.makedirs(os.path.dirname(local_dest), exist_ok=True)
                with open(local_dest, "wb") as f:
                    while chunk := stream.read(65536):
                        f.write(chunk)

            returncode = proc.wait()
            if returncode != 0:
                stderr = proc.stderr.read().decode("utf-8", errors="replace") if proc.stderr else ""
                raise BackupExecutionError(f"pg_dump failed with exit code {returncode}: {stderr}")

            backup.status = "COMPLETED"
            backup.size_bytes = stream.total_bytes
            backup.checksum_sha256 = stream.hasher.hexdigest()
            backup.completed_at = timezone.now()
            backup.save(update_fields=["status", "size_bytes", "checksum_sha256", "completed_at", "updated_at"])
            return backup

        except Exception as exc:
            if proc and proc.poll() is None:
                proc.terminate()
            if self.is_r2_configured():
                try:
                    client = self._get_r2_client()
                    client.delete_object(Bucket=self.bucket_name, Key=s3_key)
                except Exception:
                    pass
            if local_dest and os.path.exists(local_dest):
                try:
                    os.unlink(local_dest)
                except OSError:
                    pass

            backup.status = "FAILED"
            backup.error_message = str(exc)
            backup.completed_at = timezone.now()
            backup.save(update_fields=["status", "error_message", "completed_at", "updated_at"])
            raise

    def generate_presigned_download_url(
        self,
        backup: Any,
        expires_in: int = 900,
    ) -> str:
        """Generates a secure 15-minute HTTPS pre-signed download URL or local download path for a completed backup."""
        if isinstance(backup, str):
            backup = DatabaseBackup.objects.get(id=backup)

        if backup.status != "COMPLETED":
            raise ValueError("Pre-signed download URL can only be generated for completed backups.")

        if not self.is_r2_configured():
            return f"/api/v1/system/backups/{backup.id}/download/"

        client = self._get_r2_client()
        url = client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket_name, "Key": backup.s3_key},
            ExpiresIn=expires_in,
        )
        return url

    def delete_backup(self, backup: Any, actor: Any = None) -> None:
        """Deletes backup file from Cloudflare R2 or local filesystem and removes record from database."""
        if isinstance(backup, str):
            backup = DatabaseBackup.objects.get(id=backup)

        if backup.status == "IN_PROGRESS":
            raise BackupInProgressError("Cannot delete a backup currently in progress.")

        local_path = self.get_local_path(backup.s3_key)
        if os.path.isfile(local_path):
            try:
                os.unlink(local_path)
            except OSError as exc:
                logger.warning(f"Failed to delete local backup file {local_path}: {exc}")

        if self.is_r2_configured():
            try:
                client = self._get_r2_client()
                client.delete_object(Bucket=self.bucket_name, Key=backup.s3_key)
            except ClientError as exc:
                logger.warning(f"R2 delete_object error for key {backup.s3_key}: {exc}")
            except Exception as exc:
                logger.warning(f"Unexpected error while deleting R2 object {backup.s3_key}: {exc}")

        backup.delete()

    def restore_database(self, backup_id_or_file: str, confirm: bool = False) -> dict:
        """
        Safely restores PostgreSQL database from a local archive or Cloudflare R2 backup.
        Requires explicit confirm=True flag and verifies SHA-256 integrity prior to database restore.
        """
        if not confirm:
            raise ValueError("Restore execution requires explicit confirm=True confirmation.")

        cleanup_temp = False
        local_archive_path = None
        start_time = timezone.now()

        try:
            if os.path.isfile(backup_id_or_file):
                local_archive_path = backup_id_or_file
                hasher = hashlib.sha256()
                with open(local_archive_path, "rb") as f:
                    for chunk in iter(lambda: f.read(65536), b""):
                        hasher.update(chunk)
                computed_sha256 = hasher.hexdigest()
                archive_size = os.path.getsize(local_archive_path)
            else:
                backup = DatabaseBackup.objects.get(id=backup_id_or_file)
                local_path = self.get_local_path(backup.s3_key)
                if os.path.isfile(local_path):
                    local_archive_path = local_path
                    cleanup_temp = False
                else:
                    temp_file = tempfile.NamedTemporaryFile(suffix=".sql.gz", delete=False)
                    local_archive_path = temp_file.name
                    temp_file.close()
                    cleanup_temp = True

                    client = self._get_r2_client()
                    client.download_file(self.bucket_name, backup.s3_key, local_archive_path)

                hasher = hashlib.sha256()
                with open(local_archive_path, "rb") as f:
                    for chunk in iter(lambda: f.read(65536), b""):
                        hasher.update(chunk)
                computed_sha256 = hasher.hexdigest()
                archive_size = os.path.getsize(local_archive_path)

                if backup.checksum_sha256 and computed_sha256.lower() != backup.checksum_sha256.lower():
                    raise IntegrityVerificationError(
                        f"SHA-256 checksum mismatch: archive may be corrupted or altered. "
                        f"Expected {backup.checksum_sha256}, got {computed_sha256}"
                    )

            # Terminate active client connections
            if connection.vendor == "postgresql":
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                        "WHERE datname = current_database() AND pid <> pg_backend_pid();"
                    )

            # Restore database: pipe decompressed SQL to psql
            db_config = settings.DATABASES.get("default", {})
            host = db_config.get("HOST") or "127.0.0.1"
            port = str(db_config.get("PORT") or "5432")
            db_user = db_config.get("USER") or "postgres"
            db_password = db_config.get("PASSWORD") or ""
            dbname = db_config.get("NAME") or "atlas"

            env = os.environ.copy()
            if db_password:
                env["PGPASSWORD"] = db_password

            cmd = ["psql", "-h", host, "-p", port, "-U", db_user, "-d", dbname]
            with gzip.open(local_archive_path, "rb") as gz_in:
                proc = subprocess.Popen(
                    cmd,
                    stdin=gz_in,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=env,
                )
                stdout, stderr = proc.communicate()
                if proc.returncode != 0:
                    err_msg = stderr.decode("utf-8", errors="replace") if stderr else ""
                    raise RestoreExecutionError(f"psql restore failed with code {proc.returncode}: {err_msg}")

            elapsed = round((timezone.now() - start_time).total_seconds(), 2)
            return {
                "status": "SUCCESS",
                "duration_seconds": elapsed,
                "size_bytes": archive_size,
                "checksum_sha256": computed_sha256,
            }
        finally:
            if cleanup_temp and local_archive_path and os.path.exists(local_archive_path):
                try:
                    os.unlink(local_archive_path)
                except OSError:
                    pass

