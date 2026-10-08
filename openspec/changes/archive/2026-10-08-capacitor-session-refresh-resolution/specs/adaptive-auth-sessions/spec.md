## MODIFIED Requirements

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
5. `POST /api/v1/users/token/refresh/` (`CookieTokenRefreshView`): refreshes JWT tokens. The view MUST inspect the `refresh_token` HttpOnly cookie. If the cookie is absent, the view SHALL accept `refresh` from the request JSON body ONLY IF the request is identified as originating from a Capacitor/mobile client (via `X-Client-Platform: capacitor` header or Capacitor origin `capacitor://localhost`, `http://localhost`, `https://localhost`, `ionic://localhost`). Web browser requests lacking cookies MUST be rejected with HTTP 401 Unauthorized.

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

#### Scenario: Capacitor client refreshes token using request body
- GIVEN a Capacitor mobile client request to `POST /api/v1/users/token/refresh/`
- AND presenting a valid `refresh` token in the JSON request body without cookies
- AND presenting `X-Client-Platform: capacitor` or a Capacitor origin
- WHEN the request is processed
- THEN the system MUST accept the refresh token from the body and issue new tokens.

#### Scenario: Web client refresh without cookie is rejected
- GIVEN a standard web client request to `POST /api/v1/users/token/refresh/` without a refresh cookie
- AND without Capacitor identification headers or origins
- WHEN the request is processed
- THEN the system MUST reject the request with HTTP 401 Unauthorized.

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
