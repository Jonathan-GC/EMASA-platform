## 1. Core Service Local Fallback Implementation

- [x] 1.1 Add `is_r2_configured(self) -> bool` and `get_local_path(self, key: str) -> str` to `BackupService` in `Monitor_Atlas/system/services/backup_service.py`
- [x] 1.2 Implement streaming local file writing in `BackupService.create_backup` when `is_r2_configured()` is false, writing `GzipHashingStream` chunks directly to disk with atomic cleanup on failure
- [x] 1.3 Update `BackupService.restore_database` to prioritize local disk archive if present before falling back to R2 download
- [x] 1.4 Update `BackupService.delete_backup` to delete local archive file if present
- [x] 1.5 Update `BackupService.generate_presigned_download_url` to return local download route or handle local storage appropriately

## 2. API Endpoint Download Support

- [x] 2.1 Add `@action(detail=True, methods=["get"], url_path="download")` to `DatabaseBackupViewSet` in `Monitor_Atlas/system/views.py` serving local files via `FileResponse` or redirecting to R2 pre-signed URL
- [x] 2.2 Add `backups/` entry to `Monitor_Atlas/.gitignore` to ignore local backup artifacts

## 3. Test Suite Expansion & Verification

- [x] 3.1 Add unit tests in `tests/test_backup_service.py` verifying `create_backup`, `restore_database`, and `delete_backup` when R2 credentials are missing
- [x] 3.2 Add API test in `tests/test_backup_api.py` verifying download endpoint for local backup files
- [x] 3.3 Run pytest suite across all backup service and API tests to guarantee 100% pass rate
