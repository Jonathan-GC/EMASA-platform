# adaptive-auth-sessions Specification

## Purpose
Defines the adaptive risk-based authentication and user session management architecture for `Monitor_Atlas`. This specification establishes 4-tier tenant security policies (`NONE`, `LOW`, `MEDIUM`, `HIGH`), an in-memory adaptive device trust scoring engine, multi-channel multi-factor authentication (RFC 6238 TOTP, single-use hashed backup recovery codes, and email verification), active user session tracking with remote revocation and refresh token blacklisting, and a unified two-step login flow that seamlessly bypasses 2FA for recognized trusted devices while enforcing strict multi-factor verification on high-risk or policy-mandated authentications.
## Requirements
### Requirement: Tenant Security Policy Tiers
The system MUST provide a 4-tier security classification attribute `Tenant.security_level` supporting the choices `NONE`, `LOW`, `MEDIUM`, and `HIGH`:
1. `NONE`: Disables multi-factor authentication requirements for users in the tenant, permitting direct single-factor credential login.
2. `LOW`: Enforces an adaptive trust score threshold of 60. Devices scoring 60 or higher bypass 2FA prompts. Grants a 60-day device trust token time-to-live (TTL).
3. `MEDIUM` (Default): Enforces an adaptive trust score threshold of 75. Devices scoring 75 or higher bypass 2FA prompts. Grants a 30-day device trust token TTL.
4. `HIGH`: Strictly disables 2FA bypass regardless of device trust score or cookie tokens. Multi-factor authentication is mandatory on every login attempt.

The system MUST validate updates to `Tenant.security_level` to permit only defined tiers. Tenant policy resolution MUST be evaluated dynamically during authentication based on the user's assigned tenant.

#### Scenario: Default security level assigned to tenant
- GIVEN a newly created tenant without an explicit security level specification
- WHEN the tenant record is saved
- THEN the system MUST set `security_level` to `MEDIUM` by default
- AND the active policy threshold MUST evaluate to 75 with a 30-day device trust duration.

#### Scenario: Low security level permits bypass for moderate trust score
- GIVEN a tenant configured with `security_level="LOW"`
- AND an authenticated user logging into this tenant from a device evaluated with a trust score of 65
- WHEN the login credentials are submitted
- THEN the system MUST compare the score against the threshold of 60
- AND the system MUST permit 2FA bypass and issue authentication tokens directly.

#### Scenario: High security level strictly enforces 2FA regardless of score
- GIVEN a tenant configured with `security_level="HIGH"`
- AND an authenticated user logging into this tenant from a known trusted device with a maximum trust score of 100
- WHEN the user submits valid primary credentials
- THEN the system MUST reject 2FA bypass
- AND the system MUST return `requires_2fa: true` demanding multi-factor verification.

#### Scenario: None security tier bypasses 2FA completely
- GIVEN a tenant configured with `security_level="NONE"`
- WHEN a user submits valid primary credentials
- THEN the system MUST bypass all 2FA checks immediately
- AND the system MUST return JWT access and refresh tokens.

### Requirement: Adaptive Device Trust Scoring Engine
The system MUST provide an in-memory `AdaptiveTrustEngine` that evaluates risk telemetry for every login attempt and computes a normalized device trust score bounded within `[0, 100]`.

For 2FA bypass determination:
1. If tenant security level is `HIGH`, the engine MUST strictly enforce multi-factor authentication (`allow_bypass = False`) regardless of device trust or score.
2. If critical threat indicators are detected (impossible travel anomaly or suspicious/threat-flagged client IP), the engine MUST strictly enforce multi-factor authentication (`allow_bypass = False`) regardless of device trust.
3. If an unexpired, valid device trust token cookie (`device_trust_token`) matches an active session (`cookie_matched`), the engine MUST permit 2FA bypass (`allow_bypass = True`), provided neither a `HIGH` security tier nor a critical threat is active.
4. For untrusted or unrecognized devices, the engine MUST evaluate telemetry factors against the tenant's security tier threshold:
   - Valid device trust cookie: +40 points.
   - Exact client IP match: +20 points.
   - /24 Subnet match: +15 points.
   - User-Agent exact match: +15 points.
   - Recency (<7 days): +10 points.
   - Operating system mismatch: -25 points.
   - Impossible travel anomaly: -60 points.
   - Suspicious IP / threat detected: -40 points.
   The score MUST be clamped strictly between 0 and 100. 2FA bypass SHALL be permitted only if the clamped score meets or exceeds the tenant's threshold (`threshold = 60` for `LOW`, `75` for `MEDIUM`).

#### Scenario: Trusted device roaming across IP addresses bypasses 2FA
- GIVEN a tenant configured with `security_level="MEDIUM"`
- AND an incoming login request presenting a valid unexpired device trust token cookie
- AND originating from an unrecognized IP address with no prior session history
- AND without impossible travel or suspicious IP threat flags
- WHEN `AdaptiveTrustEngine` evaluates the request
- THEN the engine MUST grant 2FA bypass (`allow_bypass: true`)
- AND the decision MUST indicate bypass based on trusted device verification.

#### Scenario: Trusted device with critical threat anomaly enforces 2FA
- GIVEN a tenant configured with `security_level="MEDIUM"`
- AND an incoming login request presenting a valid unexpired device trust token cookie
- AND an impossible travel anomaly or threat-flagged IP is detected
- WHEN `AdaptiveTrustEngine` evaluates the request
- THEN the engine MUST reject 2FA bypass (`allow_bypass: false`)
- AND the system MUST require multi-factor verification.

#### Scenario: Trusted device under high security tier enforces 2FA
- GIVEN a tenant configured with `security_level="HIGH"`
- AND an incoming login request presenting a valid unexpired device trust token cookie
- WHEN `AdaptiveTrustEngine` evaluates the request
- THEN the engine MUST reject 2FA bypass (`allow_bypass: false`)
- AND the system MUST require multi-factor verification.

#### Scenario: Maximum trust score computation for recognized device on matching IP
- GIVEN an incoming login request presenting a valid device trust token cookie (+40), an identical client IP address (+20), an identical User-Agent (+15), and recorded activity 2 days ago (+10)
- WHEN `AdaptiveTrustEngine` calculates the trust score
- THEN the system MUST compute an aggregate score of 85
- AND the score MUST exceed the `MEDIUM` tenant threshold (75), allowing 2FA bypass.

#### Scenario: Impossible travel penalty triggers mandatory 2FA
- GIVEN an incoming login request presenting a valid device trust token (+40) but originating from an IP in a location 5,000 km away from a session logged 15 minutes prior
- WHEN `AdaptiveTrustEngine` evaluates the request
- THEN the engine MUST detect an impossible travel anomaly and apply a -60 penalty
- AND the resulting score MUST drop below any bypass threshold
- AND the system MUST enforce 2FA verification.

#### Scenario: Untrusted new device scoring requires 2FA
- GIVEN an incoming login request from a new device without a trust cookie (0), from an unknown IP address (0), and an unseen User-Agent (0)
- WHEN `AdaptiveTrustEngine` evaluates the request
- THEN the calculated trust score MUST be 0
- AND the system MUST enforce 2FA verification across all security tiers except `NONE`.

#### Scenario: Score clamping within valid boundary
- GIVEN an evaluation with severe negative penalties totaling -125 points
- WHEN `AdaptiveTrustEngine` finalizes the score
- THEN the score MUST be clamped to a minimum value of 0.

### Requirement: Multi-Factor Authentication with TOTP and Backup Codes
The system MUST support multi-channel multi-factor authentication through the `UserTwoFactorMethod` model, supporting method types `EMAIL`, `TOTP`, and `BACKUP_CODES`.
1. The TOTP implementation MUST strictly conform to RFC 6238 using HMAC-SHA1 with a 30-second time step and 6-digit decimal codes.
2. The system MUST generate a cryptographically random Base32-encoded secret for each TOTP method during setup.
3. The system MUST provide an `otpauth://` URI containing the secret, issuer (`settings.OTP_ISSUER` or "EMASA Monitor"), and user account identifier for QR code scanning in standard authenticator applications.
4. Code verification MUST tolerate a clock drift of ±1 time step (30 seconds before and after the current interval).
5. The system MUST generate 8 cryptographically secure single-use backup recovery codes upon TOTP activation. Backup codes MUST be stored in the database as salted cryptographic hashes and displayed to the user in plaintext only once during initial activation.
6. The system MUST provide dedicated endpoints for TOTP setup (`POST /api/v1/users/auth/mfa/totp/setup/`), activation with verification code check (`POST /api/v1/users/auth/mfa/totp/activate/`), and deactivation (`POST /api/v1/users/auth/mfa/totp/deactivate/`).
7. When a backup code is verified during authentication, it MUST immediately be marked as consumed or deleted to prevent reuse.

#### Scenario: TOTP setup generates secret and otpauth URI
- GIVEN an authenticated user without an active TOTP method
- WHEN the user sends a `POST /api/v1/users/auth/mfa/totp/setup/` request
- THEN the system MUST generate a random Base32 secret
- AND the response MUST include the plaintext secret and a valid `otpauth://` URI formatted for authenticator applications
- AND the TOTP method MUST remain in an inactive pending state until verified.

#### Scenario: TOTP activation confirms code and generates backup recovery codes
- GIVEN a user with a pending TOTP setup
- AND a valid 6-digit TOTP code generated from the pending secret
- WHEN the user sends `POST /api/v1/users/auth/mfa/totp/activate/` with the code
- THEN the system MUST verify the code against the secret
- AND the system MUST activate the TOTP method
- AND the system MUST generate 8 single-use backup recovery codes
- AND the response MUST return the 8 plaintext backup codes for user storage.

#### Scenario: TOTP verification tolerates clock drift of one time step
- GIVEN an active TOTP method with a known secret
- WHEN a verification request is received with a TOTP code corresponding to the immediately preceding time step (-30 seconds)
- THEN the system MUST accept the code as valid.

#### Scenario: Single-use consumption of backup recovery code
- GIVEN a user with active backup recovery codes
- WHEN the user authenticates using a valid plaintext backup code
- THEN the system MUST verify the code against the stored hashes
- AND the system MUST mark that specific backup code as consumed
- AND any subsequent attempt to use the same backup code MUST be rejected.

#### Scenario: TOTP deactivation disables method and revokes remaining backup codes
- GIVEN a user with an active TOTP method and remaining backup codes
- WHEN the user successfully requests deactivation via `POST /api/v1/users/auth/mfa/totp/deactivate/` confirming credentials
- THEN the TOTP method MUST be deactivated
- AND all associated backup recovery codes MUST be permanently invalidated.

### Requirement: Active User Session Tracking and Remote Revocation
The system MUST provide a `UserSession` model to track every active client login session across the platform. The model MUST record:
- `user`: ForeignKey to `User` with cascading deletion (`CASCADE`)
- `refresh_token_jti`: UUID/CharField representing the unique JWT ID of the active refresh token
- `access_token_jti`: UUID/CharField representing the unique JWT ID of the active access token
- `device_name`: CharField (e.g., "Chrome on Linux", "Safari on iOS") parsed from client User-Agent
- `trust_hash`: CharField (nullable) linking the session to a device trust token
- `ip_address`: GenericIPAddressField capturing client IP
- `user_agent`: TextField storing client User-Agent string
- `created_at`: DateTimeField recording session initiation
- `last_activity`: DateTimeField updated on token refresh or authenticated activity
- `is_active`: BooleanField indicating whether the session is currently valid

The system MUST provide REST endpoints:
1. `GET /api/v1/users/sessions/`: returns all active sessions for the authenticated user, indicating `is_current: true` for the session matching the caller's active session. The system MUST resolve the active session primarily using `session_id` from the authenticated access token (`request.auth`), falling back to the refresh cookie JTI.
2. `POST /api/v1/users/sessions/{id}/revoke/`: revokes a specific session. The system MUST mark `is_active=False` and immediately blacklist the session's tokens.
3. `POST /api/v1/users/sessions/revoke_others/`: revokes all active sessions belonging to the user except the caller's active session. The active session MUST be resolved primarily from the access token `session_id`, falling back to the refresh cookie JTI.
4. `POST /api/v1/users/sessions/trust_current/`: marks the caller's active session as trusted. The active session MUST be resolved primarily from the access token `session_id`, falling back to the refresh cookie JTI.
5. `POST /api/v1/users/token/refresh/` (`CookieTokenRefreshView`): refreshes JWT tokens. The view MUST inspect the `refresh_token` HttpOnly cookie or the request JSON body (`refresh`). If neither is present, the request MUST be rejected with HTTP 401 Unauthorized (`Refresh token not found.`).

#### Scenario: Session record created on successful login
- GIVEN a user completing authentication
- WHEN JWT access and refresh tokens are issued
- THEN the system MUST create an active `UserSession` record containing the refresh token JTI, client IP, User-Agent, and parsed device name
- AND `is_active` MUST be `True`.

#### Scenario: List user sessions identifies current session
- GIVEN an authenticated user with three active sessions across different devices
- WHEN the user sends a `GET /api/v1/users/sessions/` request
- THEN the system MUST return all three active sessions
- AND exactly one session (matching the request's refresh token JTI or access token session ID) MUST have `is_current: true`.

#### Scenario: List user sessions identifies current session via access token
- GIVEN an authenticated user making a request with a Bearer access token containing `session_id`
- AND without presenting a refresh token cookie
- WHEN the user sends a `GET /api/v1/users/sessions/` request
- THEN the system MUST identify the session matching `session_id` as `is_current: true`.

#### Scenario: Revoke others preserves current session identified via access token
- GIVEN an authenticated user with multiple active sessions making a request with a Bearer access token
- AND without presenting a refresh token cookie
- WHEN the user calls `POST /api/v1/users/sessions/revoke_others/`
- THEN all other active sessions MUST be revoked
- AND the session matching the access token's `session_id` MUST remain active.

#### Scenario: Trust current session succeeds via access token without cookies
- GIVEN an authenticated user making a request with a Bearer access token
- AND without presenting a refresh token cookie
- WHEN the user calls `POST /api/v1/users/sessions/trust_current/` with `trust=true`
- THEN the system MUST resolve the active session from the access token
- AND update the session with a device trust token.

#### Scenario: Client refreshes token using request body
- GIVEN a client request to `POST /api/v1/users/token/refresh/`
- AND presenting a valid `refresh` token in the JSON request body without cookies
- WHEN the request is processed
- THEN the system MUST accept the refresh token from the body and issue new tokens.

#### Scenario: Token refresh missing cookie and body is rejected
- GIVEN a request to `POST /api/v1/users/token/refresh/` without a refresh token cookie
- AND without a `refresh` token in the JSON request body
- WHEN the request is processed
- THEN the system MUST reject the request with HTTP 401 Unauthorized (`Refresh token not found.`).

#### Scenario: Remote revocation of a specific session blacklists refresh token
- GIVEN an active session "Session-Remote" belonging to the authenticated user
- WHEN the user calls `POST /api/v1/users/sessions/{Session-Remote-ID}/revoke/`
- THEN the system MUST set `is_active=False` on "Session-Remote"
- AND the system MUST add the `refresh_token_jti` of "Session-Remote" to SimpleJWT's blacklisted tokens
- AND any subsequent `POST /api/v1/users/token/refresh/` using that refresh token MUST return an HTTP 401 Unauthorized response.

#### Scenario: Revoke all other sessions preserves current session
- GIVEN an authenticated user with one current session and two other active sessions
- WHEN the user calls `POST /api/v1/users/sessions/revoke_others/`
- THEN the two other sessions MUST be marked `is_active=False` and their refresh tokens blacklisted
- AND the current session MUST remain `is_active=True` and its tokens valid.

#### Scenario: User session cross-account revocation prevented
- GIVEN a session belonging to "User Bob"
- AND an authenticated user "User Alice"
- WHEN "User Alice" attempts to revoke "User Bob"'s session via `POST /api/v1/users/sessions/{Bob-Session-ID}/revoke/`
- THEN the system MUST reject the request with an HTTP 404 Not Found response
- AND "User Bob"'s session MUST remain active.

### Requirement: Unified Login and Verification Flow
The system MUST provide a unified two-step adaptive login workflow through `CookieTokenObtainPairView` and `OTPVerifyView`:
1. In `CookieTokenObtainPairView` (`POST /api/v1/users/login/` or token obtain):
   - The view MUST validate primary username and password credentials.
   - The view MUST inspect the user's tenant `security_level`.
   - The view MUST invoke `AdaptiveTrustEngine` evaluating request metadata and cookies.
   - If the tenant policy allows 2FA bypass and the computed trust score meets or exceeds the tier threshold:
     - The view MUST issue JWT access and refresh tokens directly.
     - The view MUST create an active `UserSession`.
     - The view MUST return tokens and HTTP-Only cookies with payload `{"requires_2fa": false, "access": "..."}`.
   - If 2FA is required:
     - The view MUST NOT issue JWT tokens.
     - The view MUST return `{"requires_2fa": true, "available_methods": ["email", "totp", "backup_code"], "username": "..."}`.
     - If `email` is configured as a method, the view MUST dispatch an email OTP.
2. In `OTPVerifyView` (`POST /api/v1/users/auth/otp/verify/`):
   - The view MUST accept `username`, `code`, optional `method` (defaulting to auto-detection or matching active methods), and optional `trust_device` boolean.
   - The view MUST validate the code against the selected method (Email OTP, TOTP algorithm, or Backup Code hash).
   - Upon successful verification:
     - The view MUST issue JWT access and refresh tokens.
     - The view MUST create an active `UserSession`.
     - If `trust_device: true` and the tenant's security tier is not `HIGH`:
       - The view MUST generate a cryptographically random device trust token.
       - The view MUST record the device trust association with an expiration determined by the tenant tier (30 days for `MEDIUM`, 60 days for `LOW`).
       - The view MUST set the `device_trust_token` in a secure, HTTP-Only, SameSite cookie in the response.

#### Scenario: High-trust login completes in single step with 2FA bypass
- GIVEN a tenant with `security_level="MEDIUM"` (threshold 75)
- AND a user logging in from a recognized trusted device scoring 85
- WHEN the user submits valid username and password to `CookieTokenObtainPairView`
- THEN the system MUST return `requires_2fa: false`
- AND the response MUST include the JWT access token and set the refresh token cookie
- AND a new active `UserSession` MUST be recorded without prompting for 2FA.

#### Scenario: Low-trust login prompts for multi-factor verification
- GIVEN a user logging in from an unrecognized device scoring 20
- WHEN the user submits valid username and password
- THEN the system MUST return HTTP 200 with `requires_2fa: true`
- AND the response MUST include `available_methods` listing the user's configured MFA methods
- AND no JWT access or refresh tokens SHALL be issued.

#### Scenario: Verification with TOTP code and device trust establishment
- GIVEN a user prompted for 2FA with an active TOTP method
- AND the user supplies a valid 6-digit TOTP code and `trust_device=true` to `OTPVerifyView`
- THEN the system MUST verify the TOTP code
- AND the system MUST return JWT tokens
- AND the response MUST include a `Set-Cookie` header for `device_trust_token` marked `HttpOnly`, `Secure`, and `SameSite`.

#### Scenario: Verification with backup code consumes code and issues tokens
- GIVEN a user prompted for 2FA
- WHEN the user submits an unused backup recovery code to `OTPVerifyView` with `method="backup_code"`
- THEN the system MUST validate and consume the backup code
- AND the system MUST return valid JWT authentication tokens
- AND the consumed backup code MUST be permanently invalidated.

#### Scenario: Failed verification increments attempt counter and rejects
- GIVEN a user attempting 2FA verification
- WHEN an incorrect code is submitted to `OTPVerifyView`
- THEN the system MUST increment the failure counter
- AND the system MUST return an HTTP 400 Bad Request error indicating remaining attempts
- AND no authentication tokens SHALL be issued.

