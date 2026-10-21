## MODIFIED Requirements

### Requirement: Streaming Backup Execution and Cloudflare R2 Upload
The system MUST provide a `BackupService` with a `create_backup` method that performs database extraction, compression, integrity computation, and storage without buffering the entire uncompressed database dump into system RAM or intermediate uncompressed local disk storage.
1. The service MUST extract database connection parameters (host, port, database name, user, password) from `django.conf.settings.DATABASES['default']`.
2. The service MUST execute PostgreSQL's `pg_dump` utility in custom or plain SQL format via a streaming pipe.
3. The stream MUST be piped through `gzip` compression with standard compression level.
4. As compressed chunks pass through the streaming pipeline, the service MUST incrementally calculate the SHA-256 hash digest via `hashlib.sha256()`.
5. If Cloudflare R2 storage credentials (`R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_ENDPOINT_URL`, and `R2_BUCKET_NAME`) are configured, the compressed data stream MUST be uploaded to the configured Cloudflare R2 bucket using `boto3` multipart streaming upload (or `upload_fileobj`).
6. If Cloudflare R2 storage credentials or bucket are unconfigured, the service MUST transparently stream the compressed archive into local filesystem storage under the project's configured backup directory (defaulting to `backups/postgresql/YYYY/MM/`), creating parent directories automatically.
7. The service MUST count total stream bytes to determine `size_bytes`.
8. If any step in the pipeline fails (non-zero `pg_dump` exit code, broken pipe, network failure, or disk write error), the service MUST abort any pending upload or remove partial local files, set the backup status to `FAILED`, record the error traceback in `error_message`, and raise an appropriate operational error.

#### Scenario: Streaming pg_dump and gzip compression directly to R2 multipart upload
- GIVEN configured PostgreSQL credentials and valid Cloudflare R2 storage credentials in settings
- WHEN `BackupService.create_backup()` is invoked
- THEN the system MUST spawn `pg_dump` streaming stdout through gzip compression
- AND the compressed stream MUST be uploaded directly to Cloudflare R2 via `boto3` multipart upload
- AND the uncompressed database dump MUST NOT be written to a temporary local disk file.

#### Scenario: Streaming pg_dump to local filesystem when R2 is unconfigured
- GIVEN configured PostgreSQL credentials and missing or unconfigured Cloudflare R2 storage credentials
- WHEN `BackupService.create_backup()` is invoked
- THEN the system MUST detect that R2 is not configured
- AND the system MUST stream the gzip compressed archive directly into local filesystem storage
- AND compute the identical SHA-256 hash and byte count
- AND mark `DatabaseBackup.status` as `COMPLETED`.

#### Scenario: Incremental SHA-256 digest computation matches uploaded artifact
- GIVEN a backup execution streaming data to Cloudflare R2
- WHEN data chunks are read from the compression stream and transmitted to R2
- THEN the system MUST feed each chunk into an in-flight SHA-256 digest accumulator
- AND upon stream completion, the finalized digest MUST match the SHA-256 hash of the object stored in R2
- AND the 64-character lowercase hex digest MUST be saved in `DatabaseBackup.checksum_sha256`.

#### Scenario: Process execution failure terminates streaming and transitions status to FAILED
- GIVEN a backup process where `pg_dump` terminates with a non-zero exit status due to a database connection error
- WHEN the failure occurs during streaming
- THEN the service MUST catch the subprocess error
- AND the service MUST abort the active upload or remove partial local file
- AND `DatabaseBackup.status` MUST be set to `FAILED`
- AND `DatabaseBackup.error_message` MUST contain the captured stderr output from `pg_dump`.

#### Scenario: Storage upload failure triggers multipart abort and cleanup
- GIVEN a backup process where Cloudflare R2 rejects credentials or drops connection mid-stream
- WHEN `boto3` raises an S3 client exception
- THEN the service MUST terminate the `pg_dump` subprocess
- AND the service MUST abort incomplete multipart uploads for the target `s3_key`
- AND the database record MUST transition to `FAILED` status.
