# Proposal: Adaptive Authentication and User Session Management

## Why
Implement an adaptive risk-based authentication engine, 4-tier tenant security policies, multi-channel multi-factor authentication (TOTP, backup codes, and email fallback), and active user session tracking with remote revocation to eliminate friction for trusted devices while enforcing strict zero-trust controls for high-risk logins.

## What Changes
Implement 4-tier tenant security levels (`NONE`, `LOW`, `MEDIUM`, `HIGH`), active session tracking (`UserSession`) with immediate revocation and token blacklisting, adaptive risk and trust scoring engine (0-100), RFC 6238 TOTP with single-use backup recovery codes, two-step login with risk-based 2FA bypass, and contextual audit logging.

## Scope
### In Scope
- **Tenant Security Levels**: Add `Tenant.security_level` with 4 tiers (`NONE`, `LOW`, `MEDIUM`, `HIGH`) governing trust score thresholds and device trust TTLs.
- **Active User Sessions (`UserSession`)**: Track active sessions with `refresh_token_jti`, device metadata, trust tokens, and IP/user agent. Integrate with `rest_framework_simplejwt.token_blacklist` for immediate remote revocation.
- **Adaptive Risk & Trust Scoring Engine**: In-memory scoring helper (0–100) evaluating cookie trust tokens, IP match, subnet/ASN, User-Agent, usage recency, platform mismatch, impossible travel, and suspicious IP.
- **Multi-Factor Authentication (MFA)**:
  - `UserTwoFactorMethod` model supporting `EMAIL`, `TOTP`, and `BACKUP_CODES`.
  - RFC 6238-compliant TOTP engine (Base32 secrets, `otpauth://` URIs, Google Authenticator compatibility).
  - 8 single-use hashed backup recovery codes.
  - Setup, activation, and deactivation workflows for TOTP.
- **Session & Auth Endpoints**:
  - `GET /api/v1/users/sessions/`, `POST /api/v1/users/sessions/{id}/revoke/`, `POST /api/v1/users/sessions/revoke_others/`.
  - Refactored `CookieTokenObtainPairView` with risk-based 2FA bypass when score meets tenant threshold.
  - Refactored `POST /api/v1/users/auth/otp/verify/` supporting multi-method verification and device trust cookie issuance.
- **RBAC & Audit**: Register `UserSession` and `UserTwoFactorMethod` in `auditlog` and `PermissionCatalogRegistry`.

### Out of Scope
- Hardware security keys (WebAuthn / FIDO2).
- Frontend UI modifications in `Monitor_Venus`.

## Capabilities
### New Capabilities
- `adaptive-auth-sessions`: Adaptive risk-based trust scoring, 4-tier tenant security policies, multi-channel MFA (TOTP/Email/Backup Codes), and remote session management.

### Modified Capabilities
- None

## Approach
- Add `security_level` field to `Tenant` model defaulting to `MEDIUM`.
- Define `UserSession` and `UserTwoFactorMethod` models in `users/models.py`.
- Build `AdaptiveTrustEngine` computing device risk and trust scores on login.
- Implement `TOTPService` using Python standard library HMAC-SHA1 and `secrets`.
- Enhance `CookieTokenObtainPairView` to evaluate trust score against tenant security level before requiring MFA.
- Add session lifecycle management views with refresh token blacklisting on revocation.

## Affected Areas
- `Monitor_Atlas/organizations/models.py`
- `Monitor_Atlas/users/models.py`
- `Monitor_Atlas/users/serializers.py`
- `Monitor_Atlas/users/views.py`
- `Monitor_Atlas/users/urls.py`
- `Monitor_Atlas/users/services.py`
- `Monitor_Atlas/roles/catalog.py`

## Risks
- **Clock Drift in TOTP**: Clients with misaligned clocks may fail verification. *Mitigation*: Allow ±1 time-step (30-second window tolerance).
- **Session Blacklist Desync**: Revoked sessions still able to refresh tokens. *Mitigation*: Atomically blacklist `refresh_token_jti` via SimpleJWT `OutstandingToken` / `BlacklistedToken`.

## Rollback Plan
- Revert Django database migrations via `python manage.py migrate <app> <prev_migration>`.
- Revert codebase changes via Git.

## Dependencies
- `rest_framework_simplejwt.token_blacklist`
- Python `hashlib`, `hmac`, `secrets`, `base64`, `struct`, `time` (standard library)
- Django `auditlog` and `roles.catalog`

## Success Criteria
- Trusted devices exceeding tenant threshold bypass 2FA under `LOW` and `MEDIUM` security tiers.
- `HIGH` security tier strictly requires MFA regardless of trust score.
- TOTP QR setup and code validation succeed with Google Authenticator.
- Backup recovery codes work single-use and become invalid after consumption.
- Session revocation blacklists the refresh token immediately, preventing further token refresh.
- Remote session management endpoints allow viewing and revoking active sessions.
