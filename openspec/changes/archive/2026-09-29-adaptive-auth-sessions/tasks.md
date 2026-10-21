# Tasks: Adaptive Authentication and Session Management

## Review Workload Forecast
- Estimated lines: ~320-390 lines
- 400-line budget risk: Low
- Chained PRs recommended: No
- Suggested split: single-pr
Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: size-exception
400-line budget risk: Low

---

## Phase 1: Data Models & Migrations

- [x] **1.1 Add `security_level` field (`NONE`, `LOW`, `MEDIUM`, `HIGH`, default `MEDIUM`) to `Tenant` in `Monitor_Atlas/organizations/models.py`**
  - Add `SECURITY_LEVEL_CHOICES = [("NONE", "None"), ("LOW", "Low"), ("MEDIUM", "Medium"), ("HIGH", "High")]` in `Monitor_Atlas/organizations/models.py`.
  - Add `security_level = models.CharField(max_length=10, choices=SECURITY_LEVEL_CHOICES, default="MEDIUM")` to the `Tenant` model in `Monitor_Atlas/organizations/models.py`.
  - Define helper properties/methods on `Tenant` in `Monitor_Atlas/organizations/models.py` to resolve adaptive trust score threshold (`NONE`: 0, `LOW`: 60, `MEDIUM`: 75, `HIGH`: mandatory) and device trust token TTL (`LOW`: 60 days, `MEDIUM`: 30 days).

- [x] **1.2 Implement `UserSession`, `UserTwoFactorMethod`, and `UserBackupCode` models with fields and `auditlog.register` in `Monitor_Atlas/users/models.py`**
  - Define `UserSession` model in `Monitor_Atlas/users/models.py` with fields:
    - `id`: `models.CharField(max_length=16, primary_key=True, default=generate_id, editable=False)`
    - `user`: `models.ForeignKey(User, on_delete=models.CASCADE, related_name="sessions")`
    - `refresh_token_jti`: `models.CharField(max_length=255, db_index=True)`
    - `device_name`: `models.CharField(max_length=255)`
    - `trust_hash`: `models.CharField(max_length=64, null=True, blank=True, db_index=True)`
    - `ip_address`: `models.GenericIPAddressField(null=True, blank=True)`
    - `user_agent`: `models.TextField(null=True, blank=True)`
    - `created_at`: `models.DateTimeField(auto_now_add=True)`
    - `last_activity`: `models.DateTimeField(auto_now=True)`
    - `is_active`: `models.BooleanField(default=True, db_index=True)`
  - Define `UserTwoFactorMethod` model in `Monitor_Atlas/users/models.py` with fields:
    - `id`: `models.CharField(max_length=16, primary_key=True, default=generate_id, editable=False)`
    - `user`: `models.ForeignKey(User, on_delete=models.CASCADE, related_name="two_factor_methods")`
    - `method_type`: `models.CharField(max_length=20, choices=[("EMAIL", "Email"), ("TOTP", "TOTP Authenticator"), ("BACKUP_CODES", "Backup Codes")])`
    - `secret`: `models.CharField(max_length=255, null=True, blank=True)`
    - `is_active`: `models.BooleanField(default=False)`
    - `created_at`: `models.DateTimeField(auto_now_add=True)`
    - `last_used_at`: `models.DateTimeField(null=True, blank=True)`
    - `Meta.unique_together = ("user", "method_type")`
  - Define `UserBackupCode` model in `Monitor_Atlas/users/models.py` with fields:
    - `id`: `models.CharField(max_length=16, primary_key=True, default=generate_id, editable=False)`
    - `user`: `models.ForeignKey(User, on_delete=models.CASCADE, related_name="backup_codes")`
    - `code_hash`: `models.CharField(max_length=128)`
    - `is_consumed`: `models.BooleanField(default=False)`
    - `created_at`: `models.DateTimeField(auto_now_add=True)`
    - `consumed_at`: `models.DateTimeField(null=True, blank=True)`
  - Register `UserSession`, `UserTwoFactorMethod`, and `UserBackupCode` with `auditlog.registry.auditlog` in `Monitor_Atlas/users/models.py`.

- [x] **1.3 Create and apply database migrations in `Monitor_Atlas/organizations/migrations/` and `Monitor_Atlas/users/migrations/`**
  - Create migration `Monitor_Atlas/organizations/migrations/0003_tenant_security_level.py` adding `security_level` to `Tenant`.
  - Create migration `Monitor_Atlas/users/migrations/0004_adaptive_auth_sessions.py` adding `UserSession`, `UserTwoFactorMethod`, and `UserBackupCode`.
  - Apply migrations across test/development environments and verify database schema integrity.

---

## Phase 2: Core Services (Trust Engine & RFC 6238 TOTP)

- [x] **2.1 Implement standard library RFC 6238 TOTP service and backup recovery codes in `Monitor_Atlas/users/totp_service.py`**
  - Create `Monitor_Atlas/users/totp_service.py` using standard library packages (`hmac`, `hashlib`, `struct`, `base64`, `secrets`, `time`).
  - Implement `generate_totp_secret() -> str` generating Base32-encoded random secrets.
  - Implement `generate_totp_code(secret: str, time_step: int = 30) -> str` calculating 6-digit decimal TOTP codes.
  - Implement `verify_totp_code(secret: str, code: str, valid_window: int = 1, time_step: int = 30) -> bool` accepting clock drift of ±1 time-step (±30 seconds).
  - Implement `get_otpauth_uri(secret: str, username: str, issuer: str = "EMASA Monitor") -> str` constructing RFC-compliant `otpauth://` URIs for QR code provisioning.
  - Implement `generate_backup_codes(count: int = 8) -> List[Tuple[str, str]]` producing 8 random alphanumeric backup codes and their SHA-256 salted hashes.
  - Implement `verify_and_consume_backup_code(user, plaintext_code: str) -> bool` verifying against unconsumed `UserBackupCode` hashes and marking matched codes as consumed.

- [x] **2.2 Implement `AdaptiveTrustEngine` in `Monitor_Atlas/users/trust_engine.py` scoring requests [0, 100] and evaluating tenant policy thresholds**
  - Create `Monitor_Atlas/users/trust_engine.py`.
  - Implement `AdaptiveTrustEngine.evaluate(request, user, tenant_security_level)` calculating normalized trust score `[0, 100]`:
    - Add `+40` points for valid `device_trust_token` cookie matching an active session trust hash.
    - Add `+20` points for exact client IP match against prior user sessions.
    - Add `+15` points for client IP /24 subnet or ASN match when exact IP did not match.
    - Add `+15` points for exact User-Agent string match against prior sessions.
    - Add `+10` points for activity within the last 7 days from the same device/IP.
    - Deduct `-25` points for operating system or platform mismatch against registered fingerprints.
    - Deduct `-60` points for impossible travel anomaly (>800 km/h or rapid geographic shift).
    - Deduct `-40` points for datacenter, Tor, or flagged proxy IPs.
    - Clamp the aggregate score strictly within `[0, 100]`.
  - Compare computed score against tenant security level threshold (`NONE`: bypass, `LOW`: 60, `MEDIUM`: 75, `HIGH`: no bypass) to determine `requires_2fa`.

---

## Phase 3: Serializers, Views & Routing

- [x] **3.1 Create serializers for sessions, MFA, and update `OTPVerifySerializer` in `Monitor_Atlas/users/serializers.py`**
  - Implement `UserSessionSerializer` in `Monitor_Atlas/users/serializers.py` exposing session metadata and dynamic `is_current` boolean.
  - Update `OTPVerifySerializer` in `Monitor_Atlas/users/serializers.py` to support variable code formats (6-digit TOTP/email codes and backup recovery codes), optional `method` selection, and optional `trust_device` boolean.
  - Implement `TOTPSetupResponseSerializer` (`secret`, `otpauth_uri`) in `Monitor_Atlas/users/serializers.py`.
  - Implement `TOTPActivateSerializer` (`code`) in `Monitor_Atlas/users/serializers.py`.
  - Implement `TOTPDeactivateSerializer` (`password`) in `Monitor_Atlas/users/serializers.py`.

- [x] **3.2 Refactor `CookieTokenObtainPairView` in `Monitor_Atlas/users/views.py` with adaptive trust scoring and tenant policy 2FA bypass**
  - In `CookieTokenObtainPairView` in `Monitor_Atlas/users/views.py`:
    - Validate primary credentials through `CustomTokenObtainPairSerializer`.
    - Retrieve user's tenant and evaluate request using `AdaptiveTrustEngine`.
    - If trust score meets tenant policy threshold (or `security_level="NONE"`):
      - Issue JWT access and refresh tokens directly.
      - Create active `UserSession` linked to refresh token JTI and client telemetry.
      - Set HTTP-Only refresh token cookie and return HTTP 200 with `requires_2fa: false` and `access` token.
    - If 2FA is required:
      - Return HTTP 200 with `requires_2fa: true`, `username`, and `available_methods` (email, TOTP, backup code).
      - Dispatch email OTP if email is an active method for the user.

- [x] **3.3 Refactor `OTPVerifyView` in `Monitor_Atlas/users/views.py` for multi-channel MFA (TOTP, Email, Backup Code) and device trust cookie issuance**
  - In `OTPVerifyView` in `Monitor_Atlas/users/views.py`:
    - Validate payload using updated `OTPVerifySerializer`.
    - Authenticate multi-channel 2FA code based on method:
      - `EMAIL`: verify cached email OTP.
      - `TOTP`: verify against user's active `UserTwoFactorMethod` using `TOTPService.verify_totp_code`.
      - `BACKUP_CODES`: verify and consume backup code using `TOTPService.verify_and_consume_backup_code`.
    - On successful verification:
      - Issue JWT access and refresh tokens.
      - Create active `UserSession` with refresh token JTI and client device details.
      - If `trust_device=True` and tenant `security_level != "HIGH"`:
        - Generate random `device_trust_token`, store its SHA-256 hash in session `trust_hash`, and set HTTP-Only, Secure, SameSite cookie with TTL matching tenant policy (30 days for `MEDIUM`, 60 days for `LOW`).
      - Set refresh token cookie and return access token in response body.
    - On verification failure: increment attempt counter and return HTTP 400 Bad Request with remaining attempts.

- [x] **3.4 Implement `UserSessionViewSet` (list with `is_current`, revoke with token blacklist, revoke_others) and MFA views (TOTP setup, activate, deactivate) in `Monitor_Atlas/users/views.py`**
  - Implement `UserSessionViewSet(viewsets.ReadOnlyModelViewSet)` in `Monitor_Atlas/users/views.py`:
    - Restrict queries to `request.user.sessions.filter(is_active=True)`.
    - Annotate or dynamically evaluate `is_current = (session.refresh_token_jti == current_jti)`.
    - Implement `@action(detail=True, methods=["post"])` `revoke`: mark session `is_active=False` and blacklist its `refresh_token_jti` using SimpleJWT's `BlacklistedToken`.
    - Implement `@action(detail=False, methods=["post"])` `revoke_others`: mark all other active sessions of the user `is_active=False` and blacklist their refresh tokens.
  - Implement TOTP management API views in `Monitor_Atlas/users/views.py`:
    - `TOTPSetupView(APIView)`: initialize pending TOTP method and return secret with `otpauth://` URI.
    - `TOTPActivateView(APIView)`: verify code from pending setup, activate method, generate and return 8 plaintext backup codes.
    - `TOTPDeactivateView(APIView)`: re-authenticate password, deactivate TOTP method, and delete remaining backup codes.

- [x] **3.5 Register session and MFA endpoints in `Monitor_Atlas/users/urls.py`**
  - Register `sessions` router with `UserSessionViewSet` in `Monitor_Atlas/users/urls.py`.
  - Register URL patterns for `auth/mfa/totp/setup/`, `auth/mfa/totp/activate/`, and `auth/mfa/totp/deactivate/` in `Monitor_Atlas/users/urls.py`.

---

## Phase 4: Automated Testing & Verification

- [x] **4.1 Implement automated tests in `Monitor_Atlas/tests/test_adaptive_auth_sessions.py` covering tenant policies, trust scoring, TOTP verification with drift, backup code consumption, session listing, and remote revocation with SimpleJWT blacklist**
  - Create test suite `Monitor_Atlas/tests/test_adaptive_auth_sessions.py`.
  - Test tenant security tiers (`NONE`, `LOW`, `MEDIUM`, `HIGH`) and dynamic threshold enforcement.
  - Test `AdaptiveTrustEngine` score accumulation, cookie matching, IP/subnet matching, impossible travel penalties, and boundary clamping.
  - Test trusted device login bypassing 2FA on `LOW` and `MEDIUM` security tiers.
  - Test mandatory 2FA enforcement on `HIGH` security tier regardless of device trust score.
  - Test RFC 6238 TOTP generation, ±1 time-step drift tolerance, and invalid code rejection.
  - Test backup recovery code generation, single-use consumption, and code revocation upon TOTP deactivation.
  - Test `UserSessionViewSet` session listing accurately identifying `is_current: true`.
  - Test remote session revocation: verify `is_active=False` and SimpleJWT token refresh is rejected with HTTP 401 for revoked refresh token JTIs.
  - Test `revoke_others` endpoint revoking all other sessions while preserving the caller's active session.
  - Test cross-user session revocation attempts return HTTP 404 Not Found.
  - Test `auditlog.models.LogEntry` records captured for session creation, revocation, and 2FA activation/deactivation.

- [x] **4.2 Run test suite verification and mark all tasks complete**
  - Execute automated tests via Django test runner: `python manage.py test tests.test_adaptive_auth_sessions`.
  - Verify all test assertions pass cleanly with zero regressions.
