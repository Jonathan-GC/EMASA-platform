# device-measurement-consent Specification

## Purpose
Defines the versioned, measurement-granular data consent management architecture for `Monitor_Atlas`. This specification enables tenant owners and administrators to grant explicit, auditable, and revocable consent for sharing individual device telemetry variables for AI/ML model training. It specifies the measurement governance flag (`require_consent`), the versioned consent lifecycle model (`DeviceConsent`), deterministic SHA-256 cryptographic signature generation, REST endpoints for active consent inspection, acceptance, and revocation, and contextual role-based authorization with full audit logging.

## ADDED Requirements

### Requirement: Measurement Governance Flag
The system MUST include a boolean flag `require_consent` on the `Measurements` model. The flag MUST default to `True` for all existing and newly created measurement configurations, indicating that explicit data owner consent is required before telemetry variables associated with this measurement can be shared or utilized for AI/ML model training. Telemetry ingestion, API serialization, and UI governance services MUST expose `require_consent` so client interfaces can determine when user consent prompts must be triggered before data sharing is enabled.

#### Scenario: Default consent requirement on newly created measurements
- GIVEN a tenant administrator creating a new measurement configuration for a device
- WHEN the measurement record is saved without explicitly specifying `require_consent`
- THEN the system MUST set `require_consent` to `True` by default
- AND the measurement configuration MUST indicate that explicit consent is required for AI training usage.

#### Scenario: Explicit exemption of measurement variable from consent governance
- GIVEN an administrator configuring a non-sensitive or public telemetry measurement
- WHEN the administrator sets `require_consent=False` and persists the record
- THEN the system MUST save `require_consent` as `False`
- AND client interfaces querying device measurement metadata MUST receive `require_consent: false`, indicating no consent prompt is required.

#### Scenario: Serialization of consent governance status in device and measurement APIs
- GIVEN a device with multiple measurement configurations, some with `require_consent=True` and others with `require_consent=False`
- WHEN an authenticated user queries the device measurement listing endpoint
- THEN each measurement in the response payload MUST include the `require_consent` boolean field.

### Requirement: Versioned Device Consent Model
The system MUST provide a `DeviceConsent` model representing explicit consent grants for device telemetry variables. The model MUST track:
- `device`: ForeignKey to `Device` with cascading deletion (`CASCADE`)
- `tenant`: ForeignKey to `Tenant` with cascading deletion (`CASCADE`)
- `workspace`: ForeignKey to `Workspace` with cascading deletion (`CASCADE`)
- `version`: PositiveIntegerField representing the monotonically increasing consent revision (starting at 1)
- `status`: CharField supporting choices `ACTIVE`, `REVOKED`, `SUPERSEDED`
- `terms_version`: CharField recording the terms of service or consent agreement version
- `device_signature`: CharField storing the 64-character hexadecimal SHA-256 cryptographic digest
- `consented_measurements`: ManyToManyField referencing `Measurements` representing individual variable selections
- `granted_by`: ForeignKey to `User` (`SET_NULL`, nullable)
- `granted_at`: DateTimeField recording timestamp of grant
- `revoked_by`: ForeignKey to `User` (`SET_NULL`, nullable, blank)
- `revoked_at`: DateTimeField (nullable, blank)
- `revocation_reason`: TextField (nullable, blank)
- `ip_address`: GenericIPAddressField (nullable, blank)
- `user_agent`: TextField (nullable, blank)

The system MUST enforce a database-level partial `UniqueConstraint` on `(device, status)` where `status == 'ACTIVE'`, ensuring that no device can ever have more than one active consent record simultaneously.

#### Scenario: Initial consent creation establishes version 1 with ACTIVE status
- GIVEN a device in "Tenant Alpha" with no prior consent records
- WHEN an authorized user grants consent for measurements `[M1, M2]` under terms version "v1.0"
- THEN the system MUST create a `DeviceConsent` record with `version=1` and `status="ACTIVE"`
- AND `consented_measurements` MUST contain exactly `M1` and `M2`
- AND `granted_by`, `granted_at`, `ip_address`, and `user_agent` MUST be recorded.

#### Scenario: Prevention of multiple concurrent active consents via database constraint
- GIVEN an existing `DeviceConsent` record with `status="ACTIVE"` for device "DEV-01"
- WHEN an operation attempts to directly insert or update a second `DeviceConsent` record with `status="ACTIVE"` for "DEV-01"
- THEN the database partial `UniqueConstraint` MUST reject the insertion or update
- AND the transaction MUST fail with a database integrity error.

#### Scenario: Measurement validation enforces device boundary
- GIVEN a device "DEV-01" and a measurement "M-99" belonging to a different device "DEV-02"
- WHEN an authorized user attempts to create a `DeviceConsent` for "DEV-01" specifying "M-99" in `consented_measurements`
- THEN the system MUST reject the request with a validation error
- AND no consent record SHALL be created with cross-device measurement associations.

### Requirement: Cryptographic Device Signature
The system MUST compute a deterministic cryptographic SHA-256 signature (`device_signature`) upon the creation of every `DeviceConsent` record. The canonical payload for signature generation MUST concatenate:
1. Device EUI or identifier string
2. Tenant ID string
3. Consent integer version
4. Terms version string
5. Sorted, comma-separated list of consented measurement IDs
6. Granter user ID string
7. ISO-8601 UTC timestamp string of `granted_at`

The signature generation helper MUST produce a consistent 64-character lowercase hexadecimal hash. Any alteration to the consented measurements, device, tenant, version, terms version, granter, or timestamp MUST invalidate signature verification.

#### Scenario: Deterministic SHA-256 signature computation on consent acceptance
- GIVEN valid consent input data including device EUI, tenant ID, terms version "v1.0", measurements `["M2", "M1"]`, and granter user ID
- WHEN the system creates the `DeviceConsent` record
- THEN the system MUST sort the measurement IDs lexicographically into `["M1", "M2"]`
- AND the system MUST generate a SHA-256 digest over the canonical string representation
- AND the resulting digest MUST be stored in `device_signature`.

#### Scenario: Signature verification fails when canonical payload is altered
- GIVEN an existing `DeviceConsent` record with a stored `device_signature`
- WHEN a verification routine checks the signature against an altered payload where a measurement ID has been modified or removed
- THEN the recalculated SHA-256 hash MUST NOT match the stored `device_signature`
- AND the verification check MUST report a signature mismatch.

#### Scenario: Consistent signature across varying input measurement ordering
- GIVEN identical consent inputs where measurement IDs are supplied in differing orders `[M3, M1, M2]` and `[M1, M2, M3]`
- WHEN the cryptographic signature helper calculates the digest for each
- THEN both calculations MUST sort the measurement IDs prior to hashing
- AND both calculations MUST yield identical hexadecimal signatures.

### Requirement: Consent Lifecycle Endpoints
The system MUST provide dedicated REST API endpoints for managing device consent lifecycles:
1. `GET /api/v1/infrastructure/devices/{id}/consent/`: returns the current `ACTIVE` consent record for the specified device, or HTTP 404 / empty payload if no consent is active.
2. `GET /api/v1/infrastructure/devices/{id}/consent/history/`: returns the complete chronological audit history of all consent records (`ACTIVE`, `SUPERSEDED`, `REVOKED`) for the device.
3. `POST /api/v1/infrastructure/devices/{id}/consent/accept/`: accepts or updates consent for the device. If an `ACTIVE` consent record exists (version N), the operation MUST execute in an atomic transaction that transitions the existing record to `SUPERSEDED`, creates a new record with version N+1 and status `ACTIVE`, associates the specified `consented_measurements`, computes the `device_signature`, and records granter metadata (user, IP address, user agent).
4. `POST /api/v1/infrastructure/devices/{id}/consent/revoke/`: revokes the current `ACTIVE` consent for the device. The request MUST provide a non-empty `reason`. The endpoint MUST atomically transition the `ACTIVE` record to `REVOKED`, recording `revoked_by`, `revoked_at`, and `revocation_reason`. If no active consent exists, the endpoint MUST return an HTTP 400 Bad Request or HTTP 404 Not Found response.
5. `GET /api/v1/infrastructure/consents/`: returns a list of consents scoped to the request's active tenant, supporting filtering by device, status, and terms version.

#### Scenario: Retrieve active consent for a device
- GIVEN a device with an active `DeviceConsent` record at version 1
- WHEN an authorized user sends `GET /api/v1/infrastructure/devices/{id}/consent/`
- THEN the response status MUST be HTTP 200 OK
- AND the response payload MUST contain the active consent details including version, status "ACTIVE", consented measurements, and device signature.

#### Scenario: Retrieve consent when device has no active consent
- GIVEN a device with no active consent records
- WHEN an authorized user sends `GET /api/v1/infrastructure/devices/{id}/consent/`
- THEN the response status MUST indicate the absence of active consent with an HTTP 404 Not Found response.

#### Scenario: Acceptance supersedes prior active consent atomically
- GIVEN a device with an existing `ACTIVE` consent record at version 1
- WHEN an authorized user sends `POST /api/v1/infrastructure/devices/{id}/consent/accept/` with updated measurements and terms "v1.1"
- THEN within a single atomic database transaction:
  - the prior consent record MUST be transitioned to `status="SUPERSEDED"`
  - a new consent record MUST be created with `version=2`, `status="ACTIVE"`, and `terms_version="v1.1"`
- AND the response MUST return the newly created active consent record with HTTP 201 Created.

#### Scenario: Revocation of active consent with mandatory reason
- GIVEN a device with an `ACTIVE` consent record at version 2
- WHEN an authorized user sends `POST /api/v1/infrastructure/devices/{id}/consent/revoke/` with payload `{"reason": "Customer opted out of AI data sharing"}`
- THEN the consent record status MUST be transitioned to `REVOKED`
- AND `revoked_by` MUST reference the authenticated user
- AND `revoked_at` MUST be set to current timestamp
- AND `revocation_reason` MUST be saved with the provided text
- AND the response status MUST be HTTP 200 OK.

#### Scenario: Revocation rejected without reason
- GIVEN a device with an `ACTIVE` consent record
- WHEN an authorized user sends `POST /api/v1/infrastructure/devices/{id}/consent/revoke/` with an empty or missing `reason`
- THEN the system MUST reject the request with an HTTP 400 Bad Request response
- AND the active consent record MUST remain in `ACTIVE` status.

#### Scenario: Retrieve complete consent audit history
- GIVEN a device that has undergone initial grant (v1, SUPERSEDED), update (v2, SUPERSEDED), and a third grant (v3, ACTIVE)
- WHEN an authorized user sends `GET /api/v1/infrastructure/devices/{id}/consent/history/`
- THEN the response MUST return all three consent records ordered chronologically by version
- AND each record MUST include its lifecycle status, signature, granter, and timestamps.

### Requirement: Contextual Authorization and Audit Logging
The system MUST protect all consent endpoints with `HasContextualPermission` and enforce contextual role-based permissions:
- Viewing consent (`GET` endpoints): requires `view_deviceconsent` permission within the active workspace/tenant context.
- Granting or updating consent (`accept` endpoint): requires `add_deviceconsent` or `change_deviceconsent` permission.
- Revoking consent (`revoke` endpoint): requires `change_deviceconsent` permission.

The system MUST enforce strict tenant boundary isolation; cross-tenant requests attempting to access or modify device consents MUST be rejected with HTTP 404 Not Found or HTTP 403 Forbidden. `DeviceConsent` MUST be registered in `roles/catalog.py` under the `infrastructure` category, defining primary scope (`workspace`) and actions (`view`, `add`, `change`). Furthermore, the `DeviceConsent` model MUST be registered with `django-auditlog` to guarantee tamper-evident audit trail entries for every creation, status transition, and revocation.

#### Scenario: Consent viewing permitted with view_deviceconsent permission
- GIVEN an authenticated user possessing `view_deviceconsent` permission in "Workspace Alpha"
- WHEN the user requests `GET /api/v1/infrastructure/devices/{id}/consent/` for a device in "Workspace Alpha"
- THEN `HasContextualPermission` MUST grant access
- AND the consent details MUST be returned.

#### Scenario: Consent mutation denied without change_deviceconsent permission
- GIVEN an authenticated user possessing only `view_deviceconsent` and lacking `change_deviceconsent` or `add_deviceconsent`
- WHEN the user attempts `POST /api/v1/infrastructure/devices/{id}/consent/accept/` or `POST /api/v1/infrastructure/devices/{id}/consent/revoke/`
- THEN `HasContextualPermission` MUST reject the request with an HTTP 403 Forbidden response.

#### Scenario: Cross-tenant consent access denied
- GIVEN a device belonging to "Tenant Beta"
- AND an authenticated user operating with active tenant context "Tenant Alpha" without global administrative privileges
- WHEN the user attempts to access `GET /api/v1/infrastructure/devices/{id}/consent/` or post acceptance/revocation
- THEN the system MUST deny the request with an HTTP 404 Not Found or HTTP 403 Forbidden response
- AND no consent data from "Tenant Beta" SHALL be disclosed.

#### Scenario: Permission catalog registration and role mapping
- GIVEN the dynamic permission catalog initialized via `roles/catalog.py`
- WHEN the catalog registry is inspected
- THEN `deviceconsent` MUST be present as a registered resource entry under the infrastructure category
- AND its primary scope MUST be configured for workspace/tenant evaluation with `view`, `add`, and `change` actions.

#### Scenario: Audit log tracking for consent lifecycle events
- GIVEN an authorized user performing consent acceptance or revocation
- WHEN the operation completes
- THEN `django-auditlog` MUST record a `LogEntry` referencing the `DeviceConsent` object
- AND the log entry MUST capture the actor, action type, timestamp, and changed fields including `status`, `version`, and `revocation_reason`.
