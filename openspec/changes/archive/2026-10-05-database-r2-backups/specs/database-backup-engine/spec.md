# Database Backup Engine Specification

## Purpose
Defines the core persistence model, execution pipeline, storage integration, concurrency protection, and command-line interfaces for PostgreSQL database backups in `Monitor_Atlas`. This specification establishes the `DatabaseBackup` tracking model, high-efficiency streaming backups piped through gzip compression directly to Cloudflare R2 object storage with on-the-fly SHA-256 checksumming, mutex concurrency guards, and safe CLI management commands for manual backups and pre-flight verified database restorations.

## ADDED Requirements

### Requirement: Database Backup Persistence Model
The system MUST provide a `DatabaseBackup` model in `system/models.py` to record, track, and audit the lifecycle of database backup archives. The model MUST define the following fields and properties:
- `id`: UUIDField, primary key, default `uuid.uuid4`, editable `False`.
- `filename`: CharField, maximum length 255, storing the generated archive filename (formatted as `backup_YYYYMMDD_HHMMSS.sql.gz`).
- `s3_key`: CharField, maximum length 512, storing the Cloudflare R2 object key (e.g., `backups/postgresql/YYYY/MM/backup_YYYYMMDD_HHMMSS.sql.gz`).
- `size_bytes`: BigIntegerField, default 0, storing the exact size of the compressed archive in bytes.
- `checksum_sha256`: CharField, maximum length 64, storing the 64-character lowercase hexadecimal SHA-256 digest of the final compressed archive.
- `status`: CharField, choices `PENDING`, `IN_PROGRESS`, `COMPLETED`, `FAILED`, default `PENDING`.
- `trigger_type`: CharField, choices `MANUAL_CLI`, `MANUAL_API`, `AUTOMATED_SCHEDULE`.
- `triggered_by`: ForeignKey to `settings.AUTH_USER_MODEL`, null=True, blank=True, on_delete=models.SET_NULL, tracking the initiating user.
- `notes`: TextField, blank=True, default "", storing optional operator notes or backup descriptions.
- `error_message`: TextField, blank=True, default "", storing execution stack traces or diagnostic failure reasons when status is `FAILED`.
- `started_at`: DateTimeField, null=True, blank=True, recording the exact timestamp when the backup execution pipeline began.
- `completed_at`: DateTimeField, null=True, blank=True, recording the exact timestamp when the backup completed or failed.
- `created_at`: DateTimeField, auto_now_add=True.
- `updated_at`: DateTimeField, auto_now=True.

The model MUST be registered with `django-auditlog` via `auditlog.register(DatabaseBackup)` to maintain an immutable audit trail of record creation, state transitions, and deletions. The model SHOULD provide a computed property `duration_seconds` calculating the elapsed execution time between `started_at` and `completed_at`.

#### Scenario: New backup record creation in PENDING state
- GIVEN a request to initiate a new database backup
- WHEN the system initializes a `DatabaseBackup` record
- THEN the system MUST set `status` to `PENDING`
- AND `size_bytes` MUST be initialized to 0
- AND `checksum_sha256` MUST be empty
- AND `started_at` and `completed_at` MUST be `None`.

#### Scenario: Completion updates size, SHA-256 checksum, and status to COMPLETED
- GIVEN an active backup record with `status="IN_PROGRESS"`
- WHEN the streaming compression and Cloudflare R2 upload finish successfully
- THEN the system MUST update `status` to `COMPLETED`
- AND `size_bytes` MUST be set to the total byte count of the uploaded compressed archive
- AND `checksum_sha256` MUST be populated with the computed 64-character hex digest
- AND `completed_at` MUST be set to the current UTC timestamp.

#### Scenario: Execution failure updates error message and status to FAILED
- GIVEN an active backup record with `status="IN_PROGRESS"`
- WHEN an unhandled exception or process termination occurs during execution
- THEN the system MUST update `status` to `FAILED`
- AND `error_message` MUST contain the captured error details or exception traceback
- AND `completed_at` MUST be set to the current UTC timestamp.

#### Scenario: Auditlog registers state mutations and audit trail
- GIVEN an active `DatabaseBackup` instance
- WHEN any field (such as `status`, `notes`, or `completed_at`) is modified and saved
- THEN `django-auditlog` MUST record an audit log entry capturing the change diff, actor, and timestamp.

---

### Requirement: Streaming Backup Execution and Cloudflare R2 Upload
The system MUST provide a `BackupService` with a `create_backup` method that performs database extraction, compression, integrity computation, and remote object storage upload without buffering the entire uncompressed database dump into system RAM or intermediate uncompressed local disk storage.
1. The service MUST extract database connection parameters (host, port, database name, user, password) from `django.conf.settings.DATABASES['default']`.
2. The service MUST execute PostgreSQL's `pg_dump` utility in custom or plain SQL format via a streaming pipe.
3. The stream MUST be piped through `gzip` compression with standard compression level.
4. As compressed chunks pass through the streaming pipeline, the service MUST incrementally calculate the SHA-256 hash digest via `hashlib.sha256()`.
5. The compressed data stream MUST be uploaded to the configured Cloudflare R2 bucket using `boto3` multipart streaming upload (or `upload_fileobj`) configured with Cloudflare R2 endpoint URL, S3 access key, and S3 secret key.
6. The service MUST count total stream bytes to determine `size_bytes`.
7. If any step in the pipeline fails (non-zero `pg_dump` exit code, broken pipe, network failure, or R2 API rejection), the service MUST abort any pending multipart upload on Cloudflare R2, remove temporary artifacts, set the backup status to `FAILED`, record the error traceback in `error_message`, and raise an appropriate operational error.

#### Scenario: Streaming pg_dump and gzip compression directly to R2 multipart upload
- GIVEN configured PostgreSQL credentials and valid Cloudflare R2 storage credentials in settings
- WHEN `BackupService.create_backup()` is invoked
- THEN the system MUST spawn `pg_dump` streaming stdout through gzip compression
- AND the compressed stream MUST be uploaded directly to Cloudflare R2 via `boto3` multipart upload
- AND the uncompressed database dump MUST NOT be written to a temporary local disk file.

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
- AND the service MUST abort the active upload to Cloudflare R2
- AND `DatabaseBackup.status` MUST be set to `FAILED`
- AND `DatabaseBackup.error_message` MUST contain the captured stderr output from `pg_dump`.

#### Scenario: Storage upload failure triggers multipart abort and cleanup
- GIVEN a backup process where Cloudflare R2 rejects credentials or drops connection mid-stream
- WHEN `boto3` raises an S3 client exception
- THEN the service MUST terminate the `pg_dump` subprocess
- AND the service MUST abort incomplete multipart uploads for the target `s3_key`
- AND the database record MUST transition to `FAILED` status.

---

### Requirement: Concurrency Lock and Overlap Protection
The system MUST implement an atomic concurrency locking mechanism to guarantee that no two database backup processes execute simultaneously.
1. Before starting a backup, `BackupService` MUST attempt to acquire an exclusive lock (via atomic database query `select_for_update` on a dedicated lock row, atomic cache lock, or atomic status check where no record has `status="IN_PROGRESS"`).
2. If another backup process is currently in `IN_PROGRESS` status, the system MUST reject the backup request immediately without initiating `pg_dump`.
3. In service and CLI contexts, a rejection MUST raise a `BackupInProgressError`.
4. In REST API contexts, a rejection MUST produce an HTTP 409 Conflict response.
5. The lock MUST be released deterministically upon completion or failure inside a `finally` block.
6. The system MUST recognize stale locks if an `IN_PROGRESS` record has exceeded the configured maximum timeout (default 2 hours) and allow recovery or manual override.

#### Scenario: Concurrent backup attempt rejected while another backup is IN_PROGRESS
- GIVEN an existing backup "Backup-Alpha" currently running with `status="IN_PROGRESS"`
- WHEN a user or schedule triggers a second backup "Backup-Beta"
- THEN the system MUST detect the active lock
- AND the system MUST reject the second backup attempt without spawning `pg_dump`
- AND "Backup-Alpha" MUST continue executing without disruption.

#### Scenario: Lock released upon successful backup completion
- GIVEN an active backup that completes successfully with status `COMPLETED`
- WHEN the execution finishes
- THEN the system MUST release the concurrency lock
- AND subsequent backup requests MUST be allowed to execute.

#### Scenario: Lock released upon backup failure allowing recovery
- GIVEN an active backup that fails with status `FAILED`
- WHEN the failure handler completes
- THEN the system MUST release the concurrency lock in a `finally` block
- AND subsequent backup attempts MUST NOT be blocked by stale concurrency flags.

#### Scenario: Stale backup lock expiration after maximum execution timeout
- GIVEN an orphaned backup record stuck in `IN_PROGRESS` for more than 2 hours due to an unexpected worker crash
- WHEN a new backup request is received
- THEN the system MUST evaluate the timeout threshold
- AND the system MUST mark the orphaned record as `FAILED` with an error indicating execution timeout
- AND the system MUST permit the new backup to proceed.

---

### Requirement: Safe CLI Backup Command
The system MUST provide a Django management command `python manage.py backup_database` to trigger manual database backups from the command line.
1. The command MUST accept an optional `--notes` string argument to attach operator context to the backup record.
2. The command MUST execute `BackupService.create_backup(trigger_type="MANUAL_CLI", notes=notes)`.
3. The command MUST display real-time terminal progress or informative status messages.
4. Upon successful completion, the command MUST output a formatted summary containing:
   - Backup UUID (`id`)
   - Destination filename and `s3_key`
   - Final status (`COMPLETED`)
   - Archive size (human-readable string and exact bytes)
   - Computed SHA-256 checksum
   - Elapsed execution duration in seconds
   - Associated notes (if provided)
5. If the backup fails or conflicts with an ongoing run, the command MUST write the error message to `stderr` and terminate with a non-zero exit code (1).

#### Scenario: Manual CLI backup execution succeeds and outputs summary
- GIVEN a functioning PostgreSQL database and Cloudflare R2 connection
- WHEN an operator executes `python manage.py backup_database`
- THEN the command MUST trigger the backup engine with `trigger_type="MANUAL_CLI"`
- AND upon completion, the command MUST print the backup ID, S3 key, size, and SHA-256 checksum to stdout
- AND the process exit code MUST be 0.

#### Scenario: Backup command with custom notes persists notes
- GIVEN an operator executing `python manage.py backup_database --notes "Pre-upgrade snapshot v2.4.0"`
- WHEN the command executes
- THEN the system MUST persist `"Pre-upgrade snapshot v2.4.0"` into `DatabaseBackup.notes`
- AND the summary output MUST display the recorded notes.

#### Scenario: CLI backup failure outputs error to stderr and exits non-zero
- GIVEN an invalid database password or unreachable Cloudflare R2 endpoint
- WHEN an operator executes `python manage.py backup_database`
- THEN the command MUST catch the exception
- AND the command MUST print the failure details to `stderr`
- AND the process MUST exit with code 1.

---

### Requirement: Safe CLI Restore Command
The system MUST provide a Django management command `python manage.py restore_database` to safely restore PostgreSQL database backups strictly from the command line. Restoration MUST NOT be executable via REST API endpoints.
1. The command MUST accept a positional argument specifying either the `DatabaseBackup` UUID or a local archive file path.
2. The command MUST require an explicit `--confirm` flag. If `--confirm` is not supplied, the command MUST immediately abort with an explanatory warning and non-zero exit code without altering any database state.
3. If a UUID is specified, the command MUST download the archive from Cloudflare R2 into a secure local temporary file.
4. The command MUST perform pre-flight integrity verification:
   - Compute the SHA-256 digest of the downloaded or supplied archive file.
   - For UUID restores, compare the computed digest against `DatabaseBackup.checksum_sha256`.
   - If the hashes do not match exactly, the command MUST abort immediately, delete any temporary downloaded file, and display an integrity violation error without touching the database.
5. The command MUST terminate existing active client connections to the target database before restoration (executing PostgreSQL query `SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = current_database() AND pid <> pg_backend_pid();`) to prevent deadlocks or concurrent writes during restore.
6. The command MUST execute `pg_restore` (or uncompress and stream to `psql` depending on archive format) to restore database tables, schemas, indexes, and constraints.
7. Upon successful restoration, the command MUST output a detailed success confirmation and cleanly remove any temporary downloaded files.

#### Scenario: Restoration aborted without explicit confirm flag
- GIVEN a valid completed backup record "Backup-UUID-123"
- WHEN an operator executes `python manage.py restore_database Backup-UUID-123` without `--confirm`
- THEN the command MUST refuse execution
- AND the command MUST output an error demanding explicit `--confirm`
- AND no network downloads or database modifications SHALL occur
- AND the process MUST exit with a non-zero exit code.

#### Scenario: Pre-flight SHA-256 checksum mismatch halts restoration before modifying database
- GIVEN a backup record with recorded `checksum_sha256="abc..."`
- AND a downloaded or local archive whose computed SHA-256 is `"xyz..."`
- WHEN an operator executes `python manage.py restore_database Backup-UUID-123 --confirm`
- THEN the system MUST detect the SHA-256 checksum discrepancy
- AND the command MUST halt immediately before terminating connections or executing restore commands
- AND the temporary archive file MUST be deleted
- AND the process MUST exit with code 1 indicating an integrity failure.

#### Scenario: Active database connections terminated prior to restore execution
- GIVEN several active client connections connected to the target database
- AND a verified backup archive passed to `restore_database` with `--confirm`
- WHEN the restoration pipeline begins
- THEN the system MUST execute `pg_terminate_backend` for all other active connections on the target database
- AND subsequent restore statements MUST execute against a quiescent database.

#### Scenario: Successful database restore from verified Cloudflare R2 backup archive
- GIVEN a valid backup UUID with matching SHA-256 checksum and explicit `--confirm` flag
- WHEN the operator executes `python manage.py restore_database Backup-UUID-123 --confirm`
- THEN the command MUST download the archive from Cloudflare R2
- AND the command MUST verify the SHA-256 checksum successfully
- AND the command MUST terminate conflicting connections and execute `pg_restore`
- AND upon completion, temporary files MUST be purged
- AND the command MUST print a restoration confirmation summary and exit with code 0.
