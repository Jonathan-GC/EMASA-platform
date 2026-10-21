# Tasks: Database R2 Backups

## Review Workload Forecast
- Estimated lines: ~350-450 lines
- 400-line budget risk: Low
- Chained PRs recommended: No
- Suggested split: single-pr
Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: size-exception
400-line budget risk: Low

---

## Phase 1: Data Model, Migrations & Catalog Registration

- [x] **1.1 Implement `DatabaseBackup` model with 16-character ID, metadata fields, choices, computed properties, and auditlog tracking in `Monitor_Atlas/system/models.py`**
  - Create `Monitor_Atlas/system/models.py` importing `generate_id` from `organizations.hasher` and `auditlog` from `auditlog.registry`.
  - Define `STATUS_CHOICES = [("PENDING", "Pending"), ("IN_PROGRESS", "In Progress"), ("COMPLETED", "Completed"), ("FAILED", "Failed")]`.
  - Define `TRIGGER_TYPE_CHOICES = [("MANUAL_CLI", "Manual CLI"), ("MANUAL_API", "Manual API"), ("AUTOMATED_SCHEDULE", "Automated Schedule")]`.
  - Define `DatabaseBackup` model with fields:
    - `id`: `models.CharField(max_length=16, primary_key=True, default=generate_id, editable=False)`
    - `filename`: `models.CharField(max_length=255, help_text="Generated backup archive filename (e.g., backup_YYYYMMDD_HHMMSS.sql.gz)")`
    - `s3_key`: `models.CharField(max_length=512, help_text="Cloudflare R2 object key (e.g., backups/postgresql/YYYY/MM/backup_YYYYMMDD_HHMMSS.sql.gz)")`
    - `size_bytes`: `models.BigIntegerField(default=0, help_text="Exact size of the compressed archive in bytes")`
    - `checksum_sha256`: `models.CharField(max_length=64, blank=True, default="", help_text="64-character lowercase SHA-256 hex digest of the archive")`
    - `status`: `models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING", db_index=True)`
    - `trigger_type`: `models.CharField(max_length=30, choices=TRIGGER_TYPE_CHOICES, db_index=True)`
    - `triggered_by`: `models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="database_backups")`
    - `notes`: `models.TextField(blank=True, default="")`
    - `error_message`: `models.TextField(blank=True, default="")`
    - `started_at`: `models.DateTimeField(null=True, blank=True)`
    - `completed_at`: `models.DateTimeField(null=True, blank=True)`
    - `created_at`: `models.DateTimeField(auto_now_add=True, db_index=True)`
    - `updated_at`: `models.DateTimeField(auto_now=True)`
  - Implement computed property `duration_seconds` returning total runtime in seconds as a float, or `None` if either `started_at` or `completed_at` is missing.
  - Implement computed property `size_formatted` formatting `size_bytes` into a human-readable string (e.g., `B`, `KB`, `MB`, `GB`).
  - Add `Meta` class setting `ordering = ["-created_at"]`, `verbose_name = "Database Backup"`, `verbose_name_plural = "Database Backups"`.
  - Register model with `auditlog.register(DatabaseBackup)` to maintain an immutable mutation audit trail.

- [x] **1.2 Generate and run database migrations for `system` app in `Monitor_Atlas/system/migrations/`**
  - Ensure `Monitor_Atlas/system/migrations/__init__.py` exists.
  - Execute `python manage.py makemigrations system` to generate the initial migration `Monitor_Atlas/system/migrations/0001_initial.py`.
  - Run `python manage.py migrate system` and verify table creation, primary key, column types, choices, and indexes.

- [x] **1.3 Register `DatabaseBackup` in `Monitor_Atlas/roles/catalog.py` under category `infrastructure` with `global` scope**
  - Register model resource in `PermissionCatalogRegistry._initialize_defaults()` within `Monitor_Atlas/roles/catalog.py`:
    - `category_key="infrastructure"`
    - `app_label="system"`
    - `model="databasebackup"`
    - `label="Copias de Seguridad"`
    - `icon="server"`
    - `scopes=["global"]`
    - `actions=["view", "change", "delete"]`
  - Verify RBAC catalog registration via `check_permissions` or registry unit tests.

---

## Phase 2: Core Backup & Restore Service Layer

- [x] **2.1 Implement `BackupService` initialization, R2 client setup, concurrency lock management, and stale lock recovery in `Monitor_Atlas/system/services/backup_service.py`**
  - Create `Monitor_Atlas/system/services/__init__.py` and `Monitor_Atlas/system/services/backup_service.py`.
  - Define custom domain exceptions:
    - `BackupInProgressError(Exception)`
    - `BackupExecutionError(Exception)`
    - `RestoreExecutionError(Exception)`
    - `IntegrityVerificationError(Exception)`
  - Implement `BackupService` class with `_get_r2_client()` establishing `boto3.client("s3", ...)` using `settings.R2_ENDPOINT_URL`, `settings.R2_ACCESS_KEY_ID`, `settings.R2_SECRET_ACCESS_KEY`, and `settings.R2_REGION_NAME`.
  - Implement `acquire_concurrency_lock()`:
    - Query active backups where `status="IN_PROGRESS"`.
    - Evaluate stale lock recovery: if any running backup has `started_at < timezone.now() - timedelta(hours=2)` (stale threshold), transition status to `FAILED`, record `"Backup execution exceeded 2-hour timeout (stale lock recovered)"` into `error_message`, and save.
    - If any non-stale `IN_PROGRESS` backup remains, raise `BackupInProgressError("A database backup is currently in progress.")`.
  - Implement `release_concurrency_lock(backup: DatabaseBackup, new_status: str, error_message: str = "")`:
    - Safely transition backup record status (`COMPLETED` or `FAILED`), record `completed_at=timezone.now()`, save error message if any, and persist.

- [x] **2.2 Implement `create_backup()` executing streaming `pg_dump`, gzip compression, in-flight SHA-256 digest, and R2 multipart upload in `Monitor_Atlas/system/services/backup_service.py`**
  - Implement `create_backup(trigger_type: str, user=None, notes: str = "") -> DatabaseBackup`:
    - Acquire concurrency lock; create and persist `DatabaseBackup` record with `status="IN_PROGRESS"`, `started_at=timezone.now()`, `trigger_type=trigger_type`, `triggered_by=user`, `notes=notes`.
    - Generate filename `backup_YYYYMMDD_HHMMSS.sql.gz` and R2 key `backups/postgresql/YYYY/MM/backup_YYYYMMDD_HHMMSS.sql.gz`.
    - Read database credentials (`NAME`, `USER`, `PASSWORD`, `HOST`, `PORT`) from `django.conf.settings.DATABASES['default']`.
    - Launch `pg_dump` via `subprocess.Popen` with arguments `--clean --if-exists --no-owner --no-privileges`, setting `PGPASSWORD` in environment.
    - Pipe `pg_dump.stdout` through a streaming gzip compressor or chunked reader with `hashlib.sha256()`.
    - Stream compressed chunks directly into Cloudflare R2 bucket using `boto3.client.upload_fileobj` without saving uncompressed data to disk.
    - Track total streamed bytes as `size_bytes` and finalize SHA-256 lowercase hex digest.
    - Check `pg_dump` exit code: if non-zero, capture stderr and raise `BackupExecutionError`.
    - On success: persist `status="COMPLETED"`, `size_bytes=size_bytes`, `checksum_sha256=sha256_hex`, `completed_at=timezone.now()`.
    - On error/exception: abort active R2 multipart upload, terminate subprocess, persist `status="FAILED"`, `error_message=traceback_or_stderr`, and re-raise.

- [x] **2.3 Implement pre-signed URL generator and R2 object deletion in `Monitor_Atlas/system/services/backup_service.py`**
  - Implement `generate_presigned_download_url(backup: DatabaseBackup, expires_in: int = 900) -> str`:
    - Verify `backup.status == "COMPLETED"`; raise `ValueError("Pre-signed download URL can only be generated for completed backups.")` otherwise.
    - Call `boto3.client.generate_presigned_url('get_object', Params={'Bucket': bucket, 'Key': backup.s3_key}, ExpiresIn=expires_in)`.
    - Return generated HTTPS presigned URL.
  - Implement `delete_backup(backup: DatabaseBackup) -> None`:
    - Verify `backup.status != "IN_PROGRESS"`; raise `BackupInProgressError("Cannot delete a backup currently in progress.")` if active.
    - Call `boto3.client.delete_object(Bucket=bucket, Key=backup.s3_key)`, catching `botocore.exceptions.ClientError` gracefully if object is already missing.
    - Delete `backup` record from PostgreSQL database.

- [x] **2.4 Implement `restore_database()` with confirmation enforcement, SHA-256 pre-flight check, active connection termination, and `pg_restore` execution in `Monitor_Atlas/system/services/backup_service.py`**
  - Implement `restore_database(backup_id_or_file: str, confirm: bool = False) -> dict`:
    - Guard against unconfirmed execution: raise `ValueError("Restore execution requires explicit confirm=True confirmation.")` if `confirm` is `False`.
    - Resolve target archive:
      - If `backup_id_or_file` corresponds to a `DatabaseBackup.id` or UUID, fetch record from DB.
      - Download object from Cloudflare R2 to a secure temporary file (`tempfile.NamedTemporaryFile`).
      - Compute SHA-256 digest of downloaded file; compare with `backup.checksum_sha256`. If mismatched, delete temp file and raise `IntegrityVerificationError("SHA-256 checksum mismatch: archive may be corrupted or altered.")`.
      - If `backup_id_or_file` is a local file path, verify file exists and compute its SHA-256 digest.
    - Terminate active client connections: execute `SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = current_database() AND pid <> pg_backend_pid();` on target database.
    - Restore database: decompress stream and execute PostgreSQL restoration via `psql` or `pg_restore` with DB connection parameters.
    - Clean up temporary archive file in a `finally` block.
    - Return restoration summary dict with elapsed duration, archive size, and checksum verification status.

---

## Phase 3: Management Commands

- [x] **3.1 Implement manual CLI backup command in `Monitor_Atlas/system/management/commands/backup_database.py`**
  - Create `Monitor_Atlas/system/management/__init__.py`, `Monitor_Atlas/system/management/commands/__init__.py`, and `Monitor_Atlas/system/management/commands/backup_database.py`.
  - Add optional `--notes` command argument.
  - Invoke `BackupService.create_backup(trigger_type="MANUAL_CLI", notes=notes)`.
  - Render terminal output with real-time status and formatted execution summary table:
    - Backup ID (`id`)
    - Filename and S3 Key (`s3_key`)
    - Status (`COMPLETED`)
    - Size (`size_formatted` and `size_bytes`)
    - SHA-256 Checksum (`checksum_sha256`)
    - Execution Duration (`duration_seconds`)
    - Notes (if provided)
  - Handle errors: write failure details to `stderr` and exit with status code 1.

- [x] **3.2 Implement CLI restore command with confirmation gate, integrity check, and feedback in `Monitor_Atlas/system/management/commands/restore_database.py`**
  - Create `Monitor_Atlas/system/management/commands/restore_database.py`.
  - Add required positional argument `backup_id_or_file` and optional flag `--confirm`.
  - If `--confirm` is not passed:
    - Display stark warning about complete database replacement.
    - If standard input is an interactive TTY, prompt `Type 'RESTORE' to confirm: `; abort with exit code 1 if input does not match.
    - If non-interactive, print explanatory warning requiring `--confirm` and exit with code 1.
  - Invoke `BackupService.restore_database(backup_id_or_file=backup_id_or_file, confirm=True)`.
  - Display progress updates (downloading archive, verifying SHA-256 checksum, terminating connections, applying restore).
  - Print formatted success summary table to stdout upon completion.
  - Handle errors (integrity violation, connection failure): print detailed error to `stderr` and exit with code 1.

---

## Phase 4: Superuser REST API Endpoints & Serializers

- [x] **4.1 Define backup serializers for list, detail, trigger, and presigned download URL in `Monitor_Atlas/system/serializers.py`**
  - Add `DatabaseBackupSerializer` (model serializer) in `Monitor_Atlas/system/serializers.py` with fields: `id`, `filename`, `size_bytes`, `size_formatted`, `status`, `trigger_type`, `started_at`, `completed_at`, `duration_seconds`, `created_at`.
  - Add `DatabaseBackupDetailSerializer` in `Monitor_Atlas/system/serializers.py` extending `DatabaseBackupSerializer` with `s3_key`, `checksum_sha256`, `triggered_by` (nested id/username/email), `notes`, `error_message`, `updated_at`.
  - Add `CreateBackupRequestSerializer` in `Monitor_Atlas/system/serializers.py` with optional `notes = serializers.CharField(required=False, allow_blank=True, default="")`.
  - Add `DownloadUrlResponseSerializer` in `Monitor_Atlas/system/serializers.py` with fields: `download_url`, `expires_in`, `filename`, `size_bytes`, `checksum_sha256`.

- [x] **4.2 Define `IsSuperUser` permission class in `Monitor_Atlas/system/permissions.py`**
  - Create `Monitor_Atlas/system/permissions.py`.
  - Implement `IsSuperUser(BasePermission)`:
    - `has_permission(self, request, view) -> bool`: return `bool(request.user and request.user.is_authenticated and request.user.is_superuser)`.

- [x] **4.3 Implement `DatabaseBackupViewSet` with superuser access control, trigger, download URL, deletion, and restore prohibition in `Monitor_Atlas/system/views.py`**
  - Add `DatabaseBackupViewSet` in `Monitor_Atlas/system/views.py` inheriting from `viewsets.GenericViewSet`, `mixins.ListModelMixin`, `mixins.RetrieveModelMixin`, `mixins.DestroyModelMixin`.
  - Set `permission_classes = [IsAuthenticated, IsSuperUser]`.
  - Set `queryset = DatabaseBackup.objects.all().order_by("-created_at")`.
  - Support query parameter filtering for `status` and `trigger_type`, and ordering by `created_at`, `size_bytes`, `started_at`, `completed_at`.
  - Implement `create` action (`POST /api/v1/system/backups/`):
    - Validate payload with `CreateBackupRequestSerializer`.
    - Try `BackupService.create_backup(trigger_type="MANUAL_API", user=request.user, notes=notes)`.
    - Catch `BackupInProgressError` and return `HTTP 409 Conflict` with `{"detail": "A database backup is already in progress."}`.
    - Return `HTTP 201 Created` with serialized backup detail data.
  - Implement `download_url` action (`POST /api/v1/system/backups/{id}/download_url/` via `@action(detail=True, methods=["post"])`):
    - Check `backup.status == "COMPLETED"`; return `HTTP 400 Bad Request` with `{"detail": "Backup is not in completed state."}` if incomplete or failed.
    - Call `BackupService.generate_presigned_download_url(backup)`.
    - Return `HTTP 200 OK` with payload formatted by `DownloadUrlResponseSerializer`.
  - Implement `destroy` action (`DELETE /api/v1/system/backups/{id}/`):
    - If `backup.status == "IN_PROGRESS"`, return `HTTP 409 Conflict` with `{"detail": "Cannot delete a backup currently in progress."}`.
    - Call `BackupService.delete_backup(backup)` and return `HTTP 204 No Content`.
  - Implement `restore` action (`POST /api/v1/system/backups/{id}/restore/` via `@action(detail=True, methods=["post"])`):
    - Explicitly return `HTTP 405 Method Not Allowed` with `{"detail": "Database restoration via REST API is strictly forbidden. Use CLI command 'restore_database'."}`.

- [x] **4.4 Register `DatabaseBackupViewSet` router URLs in `Monitor_Atlas/system/urls.py` under `backups/`**
  - In `Monitor_Atlas/system/urls.py`, register `DatabaseBackupViewSet` on the default router: `router.register(r"backups", DatabaseBackupViewSet, basename="database-backup")`.
  - Include router URLs in `urlpatterns` alongside existing system endpoints.

---

## Phase 5: Automated Testing & Verification

- [x] **5.1 Unit and service tests for `BackupService` in `Monitor_Atlas/tests/test_backup_service.py`**
  - Create `Monitor_Atlas/tests/test_backup_service.py`.
  - Test R2 client initialization and credential loading from Django settings.
  - Test concurrency mutex lock: successful lock acquisition, rejection with `BackupInProgressError` when another backup is running.
  - Test stale lock recovery: simulate an orphaned backup in `IN_PROGRESS` older than 2 hours; verify it transitions to `FAILED` and new backup proceeds.
  - Test `create_backup()` with mocked `pg_dump` and `boto3`: verify streaming execution, gzip compression, SHA-256 calculation, multipart upload calls, and record updates (`COMPLETED`, correct `size_bytes` and `checksum_sha256`).
  - Test failure teardown: simulate subprocess non-zero exit code; verify status transitions to `FAILED`, stderr captured in `error_message`, and multipart upload aborted.
  - Test `generate_presigned_download_url()`: verify 900-second expiration, R2 client call, and rejection (ValueError) for non-completed backups.
  - Test `delete_backup()`: verify R2 `delete_object` called, DB record deleted, and rejection (`BackupInProgressError`) when in-progress.
  - Test `restore_database()`: verify `--confirm` requirement, SHA-256 checksum matching, rejection on checksum mismatch (`IntegrityVerificationError`), and invocation of `pg_terminate_backend` and `pg_restore`.

- [x] **5.2 Integration tests for management commands in `Monitor_Atlas/tests/test_backup_commands.py`**
  - Create `Monitor_Atlas/tests/test_backup_commands.py`.
  - Test `backup_database` command:
    - Successful execution prints summary table to stdout and exits with code 0.
    - Custom `--notes` persisted to database record.
    - Execution failure prints error to stderr and exits with code 1.
  - Test `restore_database` command:
    - Missing `--confirm` in non-interactive environment prints error and exits with code 1 without altering database.
    - Successful restore with `--confirm` downloads archive, verifies SHA-256, terminates connections, and prints confirmation.
    - SHA-256 checksum mismatch halts execution before database modification and exits with code 1.

- [x] **5.3 Integration tests for REST API endpoints in `Monitor_Atlas/tests/test_backup_api.py`**
  - Create `Monitor_Atlas/tests/test_backup_api.py`.
  - Test access control:
    - Authenticated superuser can access list, detail, trigger, download URL, and delete endpoints.
    - Authenticated non-superuser (standard user, tenant admin) receives `403 Forbidden` on all endpoints.
    - Unauthenticated anonymous request receives `401 Unauthorized`.
  - Test backup listing and filtering: paginated results, status filtering (`?status=COMPLETED`), trigger type filtering (`?trigger_type=MANUAL_API`), default `-created_at` ordering.
  - Test detail view: returns `size_formatted`, `duration_seconds`, and complete metadata; returns `404 Not Found` for nonexistent ID.
  - Test on-demand backup trigger (`POST /api/v1/system/backups/`): returns `201 Created` with created record; returns `409 Conflict` if a backup is already in progress.
  - Test pre-signed download URL (`POST /api/v1/system/backups/{id}/download_url/`): returns `200 OK` with 15-minute URL for completed backup; returns `400 Bad Request` for incomplete or failed backup.
  - Test backup deletion (`DELETE /api/v1/system/backups/{id}/`): returns `204 No Content` and removes R2/DB records; returns `409 Conflict` if backup is in-progress.
  - Test restore prohibition (`POST /api/v1/system/backups/{id}/restore/`): returns `405 Method Not Allowed`.

- [x] **5.4 Run full test suite and verify 0 regressions**
  - Execute `pytest Monitor_Atlas/tests/` to run all new backup test modules alongside existing platform test suites (`test_system.py`, `test_storage.py`, `test_permission_catalog.py`, `test_contextual_permissions.py`).
  - Verify 100% pass rate with zero test failures or regressions.

