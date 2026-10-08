# Feature: database-backup-local-fallback

## Objective
Implement automatic local filesystem fallback in `BackupService` when Cloudflare R2 / S3 bucket configuration or credentials are not configured or available. The service streams `pg_dump` through `GzipHashingStream` directly to a local directory (`backups/postgresql/YYYY/MM/`), maintaining identical SHA-256 integrity calculation, concurrency locking, atomic error cleanup, and supporting local file restoration and download.

## Problem & Why
Currently, `BackupService.create_backup` unconditionally attempts to initialize a `boto3` S3 client and call `upload_fileobj`. In local development, staging, or environments without Cloudflare R2 credentials setup, backup creation immediately crashes and fails. Restoring an existing backup also requires R2 unless an explicit local path is passed via CLI.

## Scope
- In Scope:
  - OpenSpec lifecycle artifacts: `proposal.md`, `design.md`, delta spec `specs/database-backup-engine/spec.md`, `tasks.md`.
  - Add `is_r2_configured(self) -> bool` and `get_local_path(self, key) -> str` to `BackupService`.
  - Add streaming local write pipeline in `create_backup` using `GzipHashingStream` when R2 is not configured.
  - Support automatic local archive resolution in `restore_database` and `delete_backup`.
  - Add direct `download` action to `DatabaseBackupViewSet` serving local backup files via `FileResponse` or redirecting to R2 pre-signed URLs.
  - Comprehensive unit and API test coverage in `tests/test_backup_service.py` and `tests/test_backup_api.py`.
  - Ensure `backups/` is excluded from git in `.gitignore`.
- Out of Scope:
  - Modifying database schema or adding new columns.
  - Celery scheduling alterations.

## Constraints & Delivery
- Delivery strategy: `ask-on-risk` (forecast < 400 lines).
- Engram mirror: Pending (Engram MCP unavailable in current session).
- Conventional commits: No AI attribution.

## Actionable Tasks

- [x] `TASK-1`: Author OpenSpec lifecycle artifacts (`proposal.md`, `design.md`, delta spec `specs/database-backup-engine/spec.md`, `tasks.md`) and validate with OpenSpec CLI.
  - Route: Direct inline
  - Trigger evidence: OpenSpec documentation generation (<10k tokens)
- [x] `TASK-2`: Refactor `BackupService` in `Monitor_Atlas/system/services/backup_service.py` to add `is_r2_configured`, streaming local creation, local restoration, and local deletion.
  - Route: Delegated direct
  - Trigger evidence: Multi-file implementation touching core system services, views, and tests
- [x] `TASK-3`: Update `DatabaseBackupViewSet` in `Monitor_Atlas/system/views.py` with unified download support for both local archives and R2 pre-signed URLs.
  - Route: Delegated direct (alongside Task 2)
  - Trigger evidence: Multi-file implementation
- [x] `TASK-4`: Expand test suite covering local fallback creation, restore, delete, and download in `tests/test_backup_service.py` and `tests/test_backup_api.py`.
  - Route: Delegated direct (alongside Task 2)
  - Trigger evidence: Multi-file verification
- [x] `TASK-5`: Run full backup test suite, generate OpenSpec `verify-report.md`, archive OpenSpec change, and create conventional work-unit commit.
  - Route: Direct inline
  - Trigger evidence: Verification and archive reporting

## Verification Evidence
- Django check: `python manage.py check` passed with 0 issues.
- Pytest suite: `venv/bin/pytest tests/test_backup_service.py tests/test_backup_api.py` passed with 40/40 tests passing (100%).
- OpenSpec validation and archive: Archived as `2026-10-08-database-backup-local-fallback` with updated main spec in `openspec/specs/database-backup-engine/spec.md`.

## Next Step
- Create conventional commit for feature closure.
