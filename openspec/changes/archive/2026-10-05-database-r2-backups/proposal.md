# Proposal: Database R2 Backups

## Intent
Implement a robust manual database backup and disaster recovery system for Monitor_Atlas using Cloudflare R2 object storage, offering CLI and Superuser REST API interfaces, pre-signed zero-egress download URLs, CLI-only restoration with SHA-256 integrity verification, and hooks for future Celery Beat automation.

## Scope
### In Scope
- **Data Model**: `DatabaseBackup` tracking backup metadata (ID, S3 key, size, SHA-256 checksum, status, trigger type, initiator, timestamps) with `django-auditlog` auditability.
- **Backup & Restore Engine (`BackupService`)**: Streaming `pg_dump` execution, gzip compression, SHA-256 digest calculation, and multipart upload to Cloudflare R2 via `boto3`.
- **Concurrency Guard**: Lock mechanism preventing overlapping backup executions.
- **CLI Commands**:
  - `backup_database`: Manual backup triggering with optional notes.
  - `restore_database`: Safe CLI-only restoration with `--confirm`, pre-flight SHA-256 checksum validation, and connection termination (`pg_terminate_backend`).
- **Superuser REST API**: Endpoints under `/api/v1/system/backups/` restricted to `is_superuser=True` for list, detail, trigger, pre-signed download URL, and deletion.
- **Task Hooks**: Clean entrypoints for future Celery/Beat scheduling.

### Out of Scope
- Frontend UI implementation in `Monitor_Venus`.
- REST API endpoint for database restoration (strictly CLI-only).
- Hermes (MongoDB) backups.

## Capabilities
### New Capabilities
- `database-backup-engine`: Core backup/restore service, PostgreSQL streaming dump/restore engine, R2 boto3 integration, SHA-256 checksumming, and CLI commands (`backup_database`, `restore_database`).
- `database-backup-api`: Superuser REST API endpoints for backup listing, triggering, status tracking, pre-signed download URL generation, and deletion with auditlog tracking.

### Modified Capabilities
- None

## Approach
1. Add `DatabaseBackup` model in `system/models.py` and register with `auditlog` and RBAC catalog.
2. Build `BackupService` managing `pg_dump`/`pg_restore` streams, R2 client via `boto3`, checksum computation, and pre-signed URL generation.
3. Implement `backup_database` and `restore_database` management commands.
4. Expose `DatabaseBackupViewSet` restricted to superusers.

## Affected Areas
- `Monitor_Atlas/system/models.py`
- `Monitor_Atlas/system/services/backup_service.py`
- `Monitor_Atlas/system/serializers.py`
- `Monitor_Atlas/system/views.py`
- `Monitor_Atlas/system/urls.py`
- `Monitor_Atlas/system/management/commands/backup_database.py`
- `Monitor_Atlas/system/management/commands/restore_database.py`
- `Monitor_Atlas/roles/catalog.py`

## Risks
- **Restore Disruption**: Accidental execution on live instances. *Mitigation*: CLI-only execution requiring explicit `--confirm` and pre-flight checksum match.
- **Concurrent Backups**: Resource exhaustion. *Mitigation*: Mutex lock rejecting overlapping runs.
- **Storage Credentials**: Misconfigured R2 settings. *Mitigation*: Pre-flight credentials verification and fail-fast logging.

## Rollback Plan
- Revert database migrations (`python manage.py migrate system <prev_migration>`).
- Revert code commits via Git.
- Clean up any orphan R2 test objects.

## Dependencies
- `boto3`
- PostgreSQL client utilities (`pg_dump`, `pg_restore`)
- `django-auditlog`

## Success Criteria
- CLI and API successfully trigger backups and store gzip archives in Cloudflare R2.
- SHA-256 checksum calculated and persisted matches downloaded archive.
- Non-superusers cannot access `/api/v1/system/backups/` endpoints.
- Database restore succeeds strictly via CLI after integrity verification.
- Concurrent backup attempts trigger conflict handling.
