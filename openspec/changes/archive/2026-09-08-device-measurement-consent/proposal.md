# Proposal: Device Measurement Consent

## Why
Implement a versioned, measurement-specific consent system enabling tenant owners and admins to grant explicit, auditable, and revocable consent for sharing individual device telemetry variables for AI model training.

## What Changes
Implement measurement governance with `require_consent` on `Measurements`, versioned `DeviceConsent` lifecycle records, SHA-256 cryptographic signatures, consent endpoints (`/consent/`, `/consent/history/`, `/consent/accept/`, `/consent/revoke/`), and contextual RBAC catalog integration with audit logging.

## Scope
### In Scope
- **Measurement Governance**: Add `require_consent` flag to `Measurements` model.
- **Versioned Consent Model (`DeviceConsent`)**:
  - Track `device`, `tenant`, `workspace`, incremental `version`, `status` (`ACTIVE`, `REVOKED`, `SUPERSEDED`), `terms_version`, `device_signature` (SHA-256), `consented_measurements` (M2M to `Measurements`), granter/revoker metadata, `revocation_reason`, IP address, and user agent.
  - Enforce partial `UniqueConstraint` on `(device, status='ACTIVE')`.
- **Cryptographic Signature**: Deterministic digest calculation over device EUI, tenant ID, version, terms version, sorted measurement IDs, granter ID, and timestamp.
- **REST Endpoints**:
  - `GET /api/v1/infrastructure/devices/{id}/consent/`: retrieve current active consent.
  - `GET /api/v1/infrastructure/devices/{id}/consent/history/`: retrieve full audit history.
  - `POST /api/v1/infrastructure/devices/{id}/consent/accept/`: grant or update consent, superseding active records.
  - `POST /api/v1/infrastructure/devices/{id}/consent/revoke/`: revoke active consent with reason.
  - `GET /api/v1/infrastructure/consents/`: tenant-scoped list of consents.
- **RBAC & Audit**: Register in `auditlog` and `PermissionCatalogRegistry`; enforce contextual permissions (`view_deviceconsent`, `add_deviceconsent`, `change_deviceconsent`).

### Out of Scope
- Downstream ML pipeline data ingestion cutoff and time-series export filtering.
- Frontend modifications in `Monitor_Venus`.

## Capabilities
### New Capabilities
- `device-measurement-consent`: Measurement-granular, versioned data consent management with cryptographic signatures and lifecycle endpoints.

### Modified Capabilities
- None

## Approach
- Add `require_consent = models.BooleanField(default=True)` to `Measurements`.
- Define `DeviceConsent` with lifecycle states, audit fields, and partial unique constraint for single active consent per device.
- Implement cryptographic SHA-256 helper generating tamper-evident digests upon acceptance.
- Add acceptance/revocation logic transitioning prior `ACTIVE` consent to `SUPERSEDED` or `REVOKED` atomically.
- Expose nested device consent actions and tenant-level consent listing secured by `HasContextualPermission`.
- Register `DeviceConsent` in `roles/catalog.py` and `auditlog`.

## Affected Areas
- `Monitor_Atlas/infrastructure/models.py`
- `Monitor_Atlas/infrastructure/serializers.py`
- `Monitor_Atlas/infrastructure/views.py`
- `Monitor_Atlas/infrastructure/urls.py`
- `Monitor_Atlas/roles/catalog.py`

## Risks
- **Race Condition on Acceptance**: Concurrent requests creating multiple active consents. *Mitigation*: Partial database `UniqueConstraint` on `(device, status='ACTIVE')` and atomic transactions.
- **Signature Drift**: Inconsistent serialization breaking digest verification. *Mitigation*: Strictly sorted measurement IDs and ISO-8601 UTC timestamp formatting.

## Rollback Plan
- Revert schema migrations using `python manage.py migrate infrastructure <prev_migration>`.
- Revert codebase changes via Git.

## Dependencies
- `organizations.models.Workspace` and `organizations.models.Tenant`
- `roles.permissions.HasContextualPermission` and `roles.catalog.PermissionCatalogRegistry`
- Django `auditlog` package

## Success Criteria
- Active consent uniquely enforced per device.
- Granting consent increments version, transitions existing to `SUPERSEDED`, and logs SHA-256 signature.
- Revocation requires a reason and updates status to `REVOKED`.
- Endpoints return 401/403 for unauthorized users and 404 across tenant boundaries.
- All consent changes are tracked in Django `auditlog`.
- Automated tests pass for model constraints, signature generation, and API flows.
