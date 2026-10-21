# Proposal: Database Backup Local Storage Fallback

## Why

Currently, `BackupService` hard-requires Cloudflare R2 / S3 storage credentials (`R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_ENDPOINT_URL`, `R2_BUCKET_NAME`). In environments without R2 configuration (e.g. local development, staging, or offline instances), triggering a backup immediately fails. The system needs a transparent local filesystem fallback that streams backups to local disk with the exact same compression and integrity guarantees.

## What Changes

- Add `is_r2_configured()` check to `BackupService`. When R2 credentials or bucket are missing, `BackupService` transparently falls back to local filesystem storage (`backups/postgresql/YYYY/MM/`).
- The local fallback streams `pg_dump` stdout through `GzipHashingStream` directly into the destination file without buffering uncompressed data into memory.
- `restore_database` checks local disk first before attempting R2 download.
- `delete_backup` safely deletes the local archive file if present.
- `DatabaseBackupViewSet` provides unified download resolution, serving local files directly via `FileResponse` and redirecting to pre-signed URLs for R2 objects.
- Add `backups/` to `.gitignore` to prevent committing local backup archives.

## Capabilities

### New Capabilities
<!-- None -->

### Modified Capabilities
- `database-backup-engine`: Support streaming local filesystem storage fallback when Cloudflare R2 object storage credentials or bucket are unconfigured.

## Impact

- Affected Code:
  - `Monitor_Atlas/system/services/backup_service.py`
  - `Monitor_Atlas/system/views.py`
  - `Monitor_Atlas/.gitignore`
- Affected Tests:
  - `Monitor_Atlas/tests/test_backup_service.py`
  - `Monitor_Atlas/tests/test_backup_api.py`
