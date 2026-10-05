from django.conf import settings
from django.db import models
from auditlog.registry import auditlog
from organizations.hasher import generate_id


STATUS_CHOICES = [
    ("PENDING", "Pending"),
    ("IN_PROGRESS", "In Progress"),
    ("COMPLETED", "Completed"),
    ("FAILED", "Failed"),
]

TRIGGER_TYPE_CHOICES = [
    ("MANUAL_CLI", "Manual CLI"),
    ("MANUAL_API", "Manual API"),
    ("AUTOMATED_SCHEDULE", "Automated Schedule"),
    ("SCHEDULED_CELERY", "Scheduled Celery"),
]


class DatabaseBackup(models.Model):
    """
    Tracks database backup archives created and stored in Cloudflare R2 / S3 storage.
    """

    id = models.CharField(
        max_length=16,
        primary_key=True,
        default=generate_id,
        editable=False,
    )
    filename = models.CharField(
        max_length=255,
        help_text="Generated backup archive filename (e.g., backup_YYYYMMDD_HHMMSS.sql.gz)",
    )
    s3_key = models.CharField(
        max_length=512,
        help_text="Cloudflare R2 object key (e.g., backups/postgresql/YYYY/MM/backup_YYYYMMDD_HHMMSS.sql.gz)",
    )
    size_bytes = models.BigIntegerField(
        default=0,
        help_text="Exact size of the compressed archive in bytes",
    )
    checksum_sha256 = models.CharField(
        max_length=64,
        blank=True,
        default="",
        help_text="64-character lowercase SHA-256 hex digest of the archive",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING",
        db_index=True,
    )
    trigger_type = models.CharField(
        max_length=30,
        choices=TRIGGER_TYPE_CHOICES,
        default="MANUAL_CLI",
        db_index=True,
    )
    triggered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="database_backups",
    )
    notes = models.TextField(
        blank=True,
        default="",
    )
    error_message = models.TextField(
        blank=True,
        default="",
    )
    started_at = models.DateTimeField(
        null=True,
        blank=True,
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Database Backup"
        verbose_name_plural = "Database Backups"

    def __str__(self) -> str:
        return f"{self.filename} ({self.status})"

    @property
    def duration_seconds(self) -> float | None:
        """
        Elapsed execution time in seconds between started_at and completed_at.
        """
        if self.started_at and self.completed_at:
            return round((self.completed_at - self.started_at).total_seconds(), 2)
        return None

    @property
    def size_formatted(self) -> str:
        """
        Human-readable string representation of size_bytes (e.g. '10.0 MB').
        """
        if not self.size_bytes or self.size_bytes <= 0:
            return "0 B"
        bytes_val = float(self.size_bytes)
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if bytes_val < 1024.0 or unit == "TB":
                if unit == "B":
                    return f"{int(bytes_val)} B"
                return f"{bytes_val:.1f} {unit}"
            bytes_val /= 1024.0
        return f"{bytes_val:.1f} PB"


auditlog.register(DatabaseBackup)
