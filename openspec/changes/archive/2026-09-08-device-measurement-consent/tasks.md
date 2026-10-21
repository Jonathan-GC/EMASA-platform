# Tasks: Device Measurement Consent

## Review Workload Forecast
- Estimated lines: ~300-380 lines
- 400-line budget risk: Low
- Chained PRs recommended: No
- Suggested split: single-pr
Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: size-exception
400-line budget risk: Low

---

## Phase 1: Data Model & Database Migrations

- [x] **1.1 Add `require_consent = models.BooleanField(default=True)` to `Measurements` in `Monitor_Atlas/infrastructure/models.py`**
  - Add `require_consent = models.BooleanField(default=True)` to the `Measurements` model in `Monitor_Atlas/infrastructure/models.py`.
  - Ensure the default value applies cleanly to existing measurement rows and future instances.
  - Maintain existing field definitions, string representations, and `auditlog` registration for `Measurements`.

- [x] **1.2 Implement `DeviceConsent` model with fields, partial `UniqueConstraint(fields=['device'], condition=models.Q(status='ACTIVE'), name='unique_active_device_consent')`, and register with `auditlog` in `Monitor_Atlas/infrastructure/models.py`**
  - Define `DeviceConsent` model in `Monitor_Atlas/infrastructure/models.py` with fields:
    - `id`: `models.CharField(max_length=16, primary_key=True, default=generate_id, editable=False)`
    - `device`: `models.ForeignKey(Device, on_delete=models.CASCADE, related_name="consents")`
    - `tenant`: `models.ForeignKey("organizations.Tenant", on_delete=models.CASCADE, related_name="device_consents")`
    - `workspace`: `models.ForeignKey("organizations.Workspace", on_delete=models.CASCADE, related_name="device_consents")`
    - `version`: `models.PositiveIntegerField(default=1)`
    - `status`: `models.CharField(max_length=20, choices=[("ACTIVE", "Active"), ("REVOKED", "Revoked"), ("SUPERSEDED", "Superseded")], default="ACTIVE")`
    - `terms_version`: `models.CharField(max_length=50)`
    - `device_signature`: `models.CharField(max_length=64)`
    - `consented_measurements`: `models.ManyToManyField(Measurements, related_name="device_consents", blank=True)`
    - `granted_by`: `models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="granted_device_consents")`
    - `granted_at`: `models.DateTimeField(auto_now_add=True)`
    - `revoked_by`: `models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="revoked_device_consents")`
    - `revoked_at`: `models.DateTimeField(null=True, blank=True)`
    - `revocation_reason`: `models.TextField(null=True, blank=True)`
    - `ip_address`: `models.GenericIPAddressField(null=True, blank=True)`
    - `user_agent`: `models.TextField(null=True, blank=True)`
  - Configure `Meta` with `ordering = ["-version"]` and partial `UniqueConstraint(fields=["device"], condition=models.Q(status="ACTIVE"), name="unique_active_device_consent")`.
  - Implement `clean()` validation on `DeviceConsent` enforcing that associated `consented_measurements` belong to the same `device`.
  - Register `DeviceConsent` with `auditlog.registry.auditlog` in `Monitor_Atlas/infrastructure/models.py`.

- [x] **1.3 Create and apply database migration in `Monitor_Atlas/infrastructure/migrations/`**
  - Generate schema migration `Monitor_Atlas/infrastructure/migrations/0006_device_measurement_consent.py`.
  - Include operations for adding `require_consent` to `Measurements`, creating table `DeviceConsent` with M2M through-table for `consented_measurements`, and applying the partial unique index constraint `unique_active_device_consent`.
  - Apply migrations to verify schema integrity and constraint enforcement.

---

## Phase 2: Cryptographic Signature Helpers & Dynamic Catalog

- [x] **2.1 Implement `compute_device_consent_signature` and `verify_device_consent_signature` in `Monitor_Atlas/infrastructure/consent_helpers.py`**
  - Create `Monitor_Atlas/infrastructure/consent_helpers.py`.
  - Implement `canonical_consent_payload(device_eui, tenant_id, version, terms_version, measurement_ids, granter_id, granted_at_iso)` sorting `measurement_ids` lexicographically and constructing canonical format `f"{device_eui}|{tenant_id}|{version}|{terms_version}|{','.join(sorted_m_ids)}|{granter_id}|{granted_at_iso}"`.
  - Implement `compute_device_consent_signature(...) -> str` returning a 64-character lowercase hexadecimal SHA-256 digest.
  - Implement `verify_device_consent_signature(consent_instance) -> bool` recalculating canonical digest and performing constant-time verification with `hmac.compare_digest()`.

- [x] **2.2 Register `deviceconsent` in `PermissionCatalogRegistry` under `infrastructure` category in `Monitor_Atlas/roles/catalog.py`**
  - In `Monitor_Atlas/roles/catalog.py`, register `deviceconsent` resource under the `infrastructure` category with `scopes=["workspace"]` and `actions=["view", "add", "change", "delete"]`.
  - Update `ResourceEntry.get_instances()` to resolve instances of `deviceconsent` using `model_class.objects.filter(workspace=workspace)`.
  - In `Monitor_Atlas/roles/permissions.py`, add `"deviceconsent"` to `WORKSPACE_SCOPED_MODELS` so `HasContextualPermission` requires workspace context for collection operations.

---

## Phase 3: Serializers, ViewSets & Routing

- [x] **3.1 Expose `require_consent` in `MeasurementsSerializer` and create `DeviceConsentSerializer`, `ConsentAcceptSerializer`, and `ConsentRevokeSerializer` in `Monitor_Atlas/infrastructure/serializers.py`**
  - In `Monitor_Atlas/infrastructure/serializers.py`, add `"require_consent"` to `MeasurementsSerializer.Meta.fields`.
  - Create `DeviceConsentSerializer` in `Monitor_Atlas/infrastructure/serializers.py` serializing all `DeviceConsent` attributes, nested measurement identifiers, and audit metadata.
  - Create `ConsentAcceptSerializer` in `Monitor_Atlas/infrastructure/serializers.py` accepting `consented_measurement_ids` (list of strings/UUIDs) and `terms_version` (string), with validation ensuring measurement IDs belong to the target device.
  - Create `ConsentRevokeSerializer` in `Monitor_Atlas/infrastructure/serializers.py` accepting mandatory non-empty `reason`.

- [x] **3.2 Add `consent`, `consent_history`, `accept_consent`, and `revoke_consent` actions on `DeviceViewSet` in `Monitor_Atlas/infrastructure/views.py` with atomic transitions and validation**
  - In `Monitor_Atlas/infrastructure/views.py`, extend `DeviceViewSet`:
    - Implement `@action(detail=True, methods=["get"], url_path="consent")` `consent`: return active `DeviceConsent` for device or HTTP 404 if no active consent exists.
    - Implement `@action(detail=True, methods=["get"], url_path="consent/history")` `consent_history`: return chronological list of all consents for the device ordered by `-version`.
    - Implement `@action(detail=True, methods=["post"], url_path="consent/accept")` `accept_consent`:
      - Validate payload using `ConsentAcceptSerializer`.
      - Execute in `transaction.atomic()` locking the `Device` row.
      - Transition any existing `ACTIVE` consent to `SUPERSEDED`.
      - Compute `version = (prior_consent.version + 1) if prior_consent else 1`.
      - Calculate deterministic signature via `compute_device_consent_signature`.
      - Extract client IP and user agent from request context.
      - Save new `DeviceConsent` with `status="ACTIVE"` and associate `consented_measurements`.
      - Return HTTP 201 Created with serialized consent payload.
    - Implement `@action(detail=True, methods=["post"], url_path="consent/revoke")` `revoke_consent`:
      - Validate payload with `ConsentRevokeSerializer`.
      - Execute in `transaction.atomic()` locking the active consent record.
      - Update active consent to `status="REVOKED"`, `revoked_by=request.user`, `revoked_at=timezone.now()`, and record `revocation_reason`.
      - Return HTTP 200 OK.

- [x] **3.3 Implement `DeviceConsentViewSet` in `Monitor_Atlas/infrastructure/views.py` for tenant-scoped consent auditing and register route in `Monitor_Atlas/infrastructure/urls.py`**
  - In `Monitor_Atlas/infrastructure/views.py`, create `DeviceConsentViewSet(viewsets.ReadOnlyModelViewSet)` with `permission_classes=[HasPermission]`, `scope="deviceconsent"`, and queryset scoped to `request.tenant` (supporting query parameter filters `device`, `status`, `terms_version`).
  - In `Monitor_Atlas/infrastructure/urls.py`, register route `routers.register(r'consents', views.DeviceConsentViewSet, basename='consent')`.

---

## Phase 4: Automated Testing & Verification

- [x] **4.1 Implement automated tests in `Monitor_Atlas/tests/test_device_measurement_consent.py` covering model constraints, deterministic signatures, accept/revoke transitions, RBAC, and audit log entries**
  - Create test suite `Monitor_Atlas/tests/test_device_measurement_consent.py`.
  - Test database partial unique constraint: inserting a second `ACTIVE` consent for the same device raises `IntegrityError`.
  - Test device boundary validation: associating measurements from other devices raises a validation error.
  - Test cryptographic helpers: verify deterministic SHA-256 calculation, sort-order invariance, and tamper detection with `verify_device_consent_signature`.
  - Test API `GET /api/v1/infrastructure/devices/{id}/consent/`: returns HTTP 200 with active consent details, or HTTP 404 when no active consent exists.
  - Test API `POST /api/v1/infrastructure/devices/{id}/consent/accept/`: atomically supersedes prior consent, creates incremented active version, and sets signature.
  - Test API `POST /api/v1/infrastructure/devices/{id}/consent/revoke/`: enforces mandatory reason, transitions active consent to `REVOKED`, and sets revoker metadata.
  - Test API `GET /api/v1/infrastructure/devices/{id}/consent/history/`: returns full chronological consent history.
  - Test contextual permissions with `HasContextualPermission`: verify users without `change_deviceconsent` receive HTTP 403 Forbidden; verify cross-tenant access returns HTTP 404.
  - Test `auditlog.models.LogEntry` captures consent creation, supersession, and revocation.

- [x] **4.2 Run test suite verification and mark all tasks complete**
  - Execute automated tests via Django test runner: `python manage.py test tests.test_device_measurement_consent`.
  - Verify all test assertions pass cleanly with zero regressions.
