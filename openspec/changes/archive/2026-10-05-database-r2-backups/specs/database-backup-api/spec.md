# Database Backup API Specification

## Purpose
Defines the REST API interface for database backup management in `Monitor_Atlas`. This specification establishes strict superuser-only access control, paginated backup history listing and filtering, detailed runtime and size status inspection, on-demand backup initiation with concurrency conflict safeguards, secure 15-minute pre-signed download URL generation directly against Cloudflare R2 object storage, and synchronized backup deletion with remote storage cleanup and audit logging.

## ADDED Requirements

### Requirement: Superuser-Restricted Backup Access Control
The system MUST provide a `DatabaseBackupViewSet` mapped under `/api/v1/system/backups/` that strictly restricts access to authenticated platform superusers (`is_superuser=True`).
1. All endpoints under `/api/v1/system/backups/` MUST enforce `permissions.IsAuthenticated` and a custom permission class `IsSuperUser` (verifying `request.user.is_superuser is True`).
2. Any request from an unauthenticated caller MUST be rejected with HTTP 401 Unauthorized.
3. Any request from an authenticated user who is not a superuser—including regular users, workspace administrators, and tenant administrators—MUST be rejected with HTTP 403 Forbidden.
4. Database restoration MUST NOT be exposed via any REST API endpoint or action. Any HTTP request attempting to invoke restore actions via the API MUST be rejected with HTTP 405 Method Not Allowed or HTTP 404 Not Found.

#### Scenario: Superuser granted full access to backup endpoints
- GIVEN an authenticated user with `is_superuser=True`
- WHEN the user sends an HTTP request to any endpoint under `/api/v1/system/backups/`
- THEN the system MUST permit access
- AND the request MUST proceed to the respective view handler.

#### Scenario: Authenticated non-superuser user rejected with 403 Forbidden
- GIVEN an authenticated user with `is_superuser=False` and standard member permissions
- WHEN the user sends a `GET /api/v1/system/backups/` request
- THEN the system MUST reject the request with an HTTP 403 Forbidden response
- AND no backup metadata SHALL be revealed.

#### Scenario: Tenant administrator rejected with 403 Forbidden
- GIVEN an authenticated user who possesses tenant administrator privileges within their tenant but has `is_superuser=False`
- WHEN the user sends a `GET` or `POST` request to `/api/v1/system/backups/`
- THEN the system MUST reject the request with an HTTP 403 Forbidden response.

#### Scenario: Unauthenticated request rejected with 401 Unauthorized
- GIVEN an anonymous unauthenticated request
- WHEN the request is sent to `/api/v1/system/backups/`
- THEN the system MUST reject the request with an HTTP 401 Unauthorized response.

#### Scenario: Restore action unavailable on REST API returning 405 Method Not Allowed
- GIVEN an authenticated superuser
- WHEN the user attempts to send a `POST /api/v1/system/backups/{id}/restore/` request
- THEN the system MUST reject the request with an HTTP 405 Method Not Allowed or HTTP 404 Not Found response
- AND the system MUST NOT trigger any database restore operation.

---

### Requirement: Backup Listing and Detailed Status Retrieval
The system MUST provide endpoints to query and inspect backup records with pagination, filtering, ordering, and execution duration calculation.
1. `GET /api/v1/system/backups/`:
   - MUST return a paginated list of `DatabaseBackup` records using standard pagination (`count`, `next`, `previous`, `results`).
   - MUST order results chronologically descending by default (`-created_at`).
   - MUST support ordering by `created_at`, `size_bytes`, `started_at`, and `completed_at`.
   - MUST support query parameter filtering by `status` (`PENDING`, `IN_PROGRESS`, `COMPLETED`, `FAILED`).
   - MUST support query parameter filtering by `trigger_type` (`MANUAL_CLI`, `MANUAL_API`, `AUTOMATED_SCHEDULE`).
2. `GET /api/v1/system/backups/{id}/`:
   - MUST return the comprehensive details of a single backup record identified by UUID.
   - The response payload MUST include:
     - `id`: UUID
     - `filename`: String
     - `s3_key`: String
     - `size_bytes`: Integer
     - `size_formatted`: String (human-readable string representation, e.g. "45.2 MB")
     - `checksum_sha256`: String (64-character lowercase hex digest)
     - `status`: String
     - `trigger_type`: String
     - `triggered_by`: Object or null, containing `id`, `username`, and `email` of the initiating user
     - `notes`: String
     - `error_message`: String (populated if status is `FAILED`)
     - `started_at`: ISO-8601 DateTime or null
     - `completed_at`: ISO-8601 DateTime or null
     - `duration_seconds`: Float or null (computed runtime between `started_at` and `completed_at`)
     - `created_at`: ISO-8601 DateTime
     - `updated_at`: ISO-8601 DateTime
3. If the requested backup UUID does not exist, the endpoint MUST return HTTP 404 Not Found.

#### Scenario: Paginated backup list ordered chronologically descending
- GIVEN multiple existing database backup records in the system
- WHEN a superuser sends a `GET /api/v1/system/backups/` request
- THEN the system MUST return an HTTP 200 OK response with paginated results
- AND the results MUST be ordered with the most recent backup first.

#### Scenario: Backup listing filtered by status
- GIVEN existing database backup records with statuses `COMPLETED`, `FAILED`, and `IN_PROGRESS`
- WHEN a superuser sends `GET /api/v1/system/backups/?status=COMPLETED`
- THEN the system MUST return only records having `status="COMPLETED"`.

#### Scenario: Backup listing filtered by trigger type
- GIVEN existing backup records triggered via CLI, API, and schedule
- WHEN a superuser sends `GET /api/v1/system/backups/?trigger_type=MANUAL_API`
- THEN the system MUST return only records where `trigger_type="MANUAL_API"`.

#### Scenario: Backup detail view includes runtime duration and formatted size
- GIVEN a completed backup record with `size_bytes=10485760` (10 MB), `started_at="2026-10-05T12:00:00Z"`, and `completed_at="2026-10-05T12:00:45Z"`
- WHEN a superuser sends `GET /api/v1/system/backups/{id}/`
- THEN the response payload MUST contain `size_formatted="10.0 MB"`
- AND `duration_seconds` MUST evaluate to `45.0`
- AND `checksum_sha256` MUST be returned.

#### Scenario: Non-existent backup detail request returns 404 Not Found
- GIVEN a non-existent UUID `00000000-0000-0000-0000-000000000000`
- WHEN a superuser sends `GET /api/v1/system/backups/00000000-0000-0000-0000-000000000000/`
- THEN the system MUST return an HTTP 404 Not Found response.

---

### Requirement: On-Demand Backup Triggering via API
The system MUST provide an endpoint `POST /api/v1/system/backups/` allowing superusers to trigger manual database backups on demand.
1. The request body MAY contain an optional JSON payload with a `notes` string field.
2. The view MUST check the global backup concurrency lock before execution:
   - If another backup is currently `IN_PROGRESS`, the endpoint MUST return an HTTP 409 Conflict response containing an error message explaining that a backup is already running.
3. If no backup is running, the endpoint MUST create a new `DatabaseBackup` record with `trigger_type="MANUAL_API"`, `triggered_by=request.user`, and `notes` populated from the request payload.
4. The system MUST execute the backup pipeline via `BackupService.create_backup`.
5. Upon successful creation and start/completion, the endpoint MUST return an HTTP 201 Created response (or 202 Accepted if queued via asynchronous worker) containing the serialized backup record.
6. The trigger action and record creation MUST be captured in `django-auditlog`.

#### Scenario: On-demand backup trigger initiates execution and returns 201 Created
- GIVEN no other database backup currently running
- WHEN an authenticated superuser sends a `POST /api/v1/system/backups/` request
- THEN the system MUST create a new `DatabaseBackup` record
- AND the system MUST return an HTTP 201 Created response containing the serialized backup metadata
- AND the backup record MUST transition to `COMPLETED` upon successful stream and upload.

#### Scenario: Concurrent on-demand backup trigger rejected with 409 Conflict
- GIVEN a database backup already actively executing with status `IN_PROGRESS`
- WHEN an authenticated superuser sends a `POST /api/v1/system/backups/` request
- THEN the system MUST reject the request with an HTTP 409 Conflict response
- AND the response body MUST indicate that a backup is currently in progress
- AND no new `DatabaseBackup` record SHALL be created.

#### Scenario: API trigger records requesting user and provided notes
- GIVEN an authenticated superuser "admin_operator"
- WHEN the user sends `POST /api/v1/system/backups/` with body `{"notes": "Snapshot before system migration"}`
- THEN the created `DatabaseBackup` record MUST have `triggered_by` set to "admin_operator"
- AND `notes` MUST be set to `"Snapshot before system migration"`
- AND `trigger_type` MUST be set to `"MANUAL_API"`.

---

### Requirement: Secure Pre-Signed Download URL Generation
The system MUST provide an action endpoint `POST /api/v1/system/backups/{id}/download_url/` allowing superusers to generate time-limited pre-signed download URLs for completed backups.
1. The endpoint MUST verify that the requested backup has `status="COMPLETED"`.
2. If `status` is `PENDING`, `IN_PROGRESS`, or `FAILED`, the endpoint MUST reject the request with an HTTP 400 Bad Request response indicating that the backup is not in a completed downloadable state.
3. The service MUST use `boto3` to generate an S3 pre-signed `get_object` URL pointing to the Cloudflare R2 bucket and `s3_key`.
4. The expiration of the pre-signed URL MUST be set to exactly 900 seconds (15 minutes).
5. The endpoint response payload MUST return:
   - `download_url`: String (the HTTPS pre-signed Cloudflare R2 URL)
   - `expires_in`: Integer (900)
   - `filename`: String
   - `size_bytes`: Integer
   - `checksum_sha256`: String
6. The archive download MUST be served directly by Cloudflare R2, offloading bandwidth and egress costs from the application server.
7. The URL generation event MUST be recorded in the system audit log.

#### Scenario: Generation of 15-minute pre-signed download URL for completed backup
- GIVEN a database backup record with `status="COMPLETED"` and a valid `s3_key`
- WHEN an authenticated superuser sends a `POST /api/v1/system/backups/{id}/download_url/` request
- THEN the system MUST return an HTTP 200 OK response
- AND the response payload MUST contain a `download_url` pointing to Cloudflare R2
- AND `expires_in` MUST be `900`
- AND the response MUST include `filename`, `size_bytes`, and `checksum_sha256`.

#### Scenario: Download URL generation rejected for incomplete or failed backup
- GIVEN a backup record with `status="FAILED"` or `status="IN_PROGRESS"`
- WHEN a superuser sends `POST /api/v1/system/backups/{id}/download_url/`
- THEN the system MUST reject the request with an HTTP 400 Bad Request response
- AND no pre-signed URL SHALL be generated.

#### Scenario: Pre-signed download generation event recorded in auditlog
- GIVEN an authenticated superuser requesting a download URL for a completed backup
- WHEN the endpoint generates the pre-signed URL
- THEN the system MUST log an audit entry documenting the user, timestamp, and backup ID accessed.

---

### Requirement: Backup Deletion and Cloudflare R2 Cleanup
The system MUST provide an endpoint `DELETE /api/v1/system/backups/{id}/` allowing superusers to delete a backup record and purge its remote storage object.
1. The endpoint MUST verify that the backup is NOT currently `IN_PROGRESS`. If the backup is in progress, the deletion MUST be rejected with an HTTP 409 Conflict response.
2. The service MUST invoke `boto3` client to delete the object corresponding to `s3_key` from the Cloudflare R2 bucket.
3. If the object does not exist in Cloudflare R2 (e.g., due to an earlier manual deletion or upload failure), the service MUST handle the storage response gracefully without raising an unhandled exception.
4. The endpoint MUST delete the `DatabaseBackup` record from the PostgreSQL database.
5. The endpoint MUST return an HTTP 204 No Content response upon successful deletion.
6. The deletion event, including the initiating superuser, backup ID, and S3 key, MUST be recorded in `django-auditlog`.

#### Scenario: Backup deletion removes R2 object and database record returning 204 No Content
- GIVEN an existing completed backup record with its associated archive stored in Cloudflare R2
- WHEN an authenticated superuser sends a `DELETE /api/v1/system/backups/{id}/` request
- THEN the system MUST delete the archive object from Cloudflare R2 via `boto3`
- AND the system MUST delete the `DatabaseBackup` record from the database
- AND the endpoint MUST return an HTTP 204 No Content response.

#### Scenario: Deletion of in-progress backup rejected with 409 Conflict
- GIVEN a backup record currently in `IN_PROGRESS` status
- WHEN a superuser sends `DELETE /api/v1/system/backups/{id}/`
- THEN the system MUST reject the deletion request with an HTTP 409 Conflict response
- AND the active backup process and database record MUST remain intact.

#### Scenario: Deletion event recorded in auditlog with backup identifier and S3 key
- GIVEN an authenticated superuser deleting a backup record
- WHEN the deletion is processed
- THEN `django-auditlog` MUST record a deletion audit entry containing the user ID, backup UUID, and the deleted `s3_key`.
