# Design: Database Backup Local Storage Fallback

## Context

See [proposal.md](file:///home/weedopc/Projects/EMASA-platform/openspec/changes/database-backup-local-fallback/proposal.md).
Currently, `BackupService` in `Monitor_Atlas/system/services/backup_service.py` requires Cloudflare R2 / S3 storage credentials (`R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_ENDPOINT_URL`, `R2_BUCKET_NAME`). When these settings are absent or empty (typical in local development, staging, or offline environments), calling `create_backup` crashes upon initializing `boto3` or calling `upload_fileobj`. Similarly, restoring an archive fails unless an explicit local path is given, and backups cannot be deleted or downloaded cleanly without R2.

## Goals / Non-Goals

**Goals:**
- Detect when Cloudflare R2 is unconfigured (`is_r2_configured(self) -> bool`).
- When R2 is unconfigured, stream `pg_dump` stdout through `GzipHashingStream` directly into a local file (`backups/postgresql/YYYY/MM/filename.sql.gz`) under the project's base directory or configured backup root, calculating SHA-256 and byte size on the fly without RAM buffering.
- Ensure partial or corrupted files on disk are removed if `pg_dump` fails or an exception occurs during streaming.
- Support `restore_database` by automatically checking for the local file on disk before attempting an R2 download.
- Support `delete_backup` by removing the file on disk if it exists, alongside R2 object deletion if R2 is configured.
- Provide a unified download mechanism in `DatabaseBackupViewSet` that serves the local archive file directly via `FileResponse` when stored locally or redirects to a pre-signed URL when in R2.
- Exclude `backups/` in `Monitor_Atlas/.gitignore`.

**Non-Goals:**
- Changing database backup models or adding schema migrations.
- Changing Celery task signatures or scheduling parameters.
- Supporting arbitrary third-party cloud storage backends beyond S3/R2 and local disk.

## Decisions

### Decision 1: Transparent Fallback Detection via `is_r2_configured`
- **Chosen**: Check presence and non-emptiness of `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_ENDPOINT_URL`, and `R2_BUCKET_NAME` from `django.conf.settings`.
- **Rationale**: Keeps the configuration declarative and avoids crashing when developers run the system locally without cloud credentials.

### Decision 2: Chunked Local Streaming via `GzipHashingStream`
- **Chosen**: In `create_backup()`, if `not self.is_r2_configured()`, open destination file in write-binary mode and stream in 64KB chunks (`while chunk := stream.read(65536): f.write(chunk)`).
- **Rationale**: `GzipHashingStream` is an in-flight wrapper that compresses `pg_dump`'s stdout while hashing and counting bytes. Writing chunk-by-chunk maintains $O(1)$ memory consumption and generates identical SHA-256 digests and file sizes whether saved locally or uploaded to R2.

### Decision 3: Local Path Mapping
- **Chosen**: Store backups at `os.path.join(getattr(settings, "BACKUP_LOCAL_DIR", None) or settings.BASE_DIR, backup.s3_key)`.
- **Rationale**: The `s3_key` is already formatted as `backups/postgresql/YYYY/MM/<filename>.sql.gz`. Reusing this structure on disk keeps directory organization neat and ensures 1:1 mapping between storage key and filesystem path.

### Decision 4: Unified Download in ViewSet
- **Chosen**: In `DatabaseBackupViewSet`, implement a `download` action:
  - If backup exists locally on disk: return `FileResponse(open(path, "rb"), as_attachment=True, filename=backup.filename)`.
  - Else if R2 is configured: redirect to or return pre-signed download URL.
  - Else: return 404 / 400 with a clear error.
- **Rationale**: Allows the frontend or administrator to download the backup file seamlessly through the REST API regardless of where it is stored.

## Risks / Trade-offs

- **[Risk] Local disk space exhaustion**:
  - *Mitigation*: Existing retention policies and `delete_backup` clean up obsolete backups. Ensure atomic removal on failure so orphaned incomplete backups do not accumulate.
- **[Risk] Path traversal when resolving local path**:
  - *Mitigation*: Derive path strictly from sanitized `s3_key` generated internally by `BackupService` (`backups/postgresql/...`).

## Migration Plan

Zero database migrations required. Purely service and view level enhancements with zero schema changes.
