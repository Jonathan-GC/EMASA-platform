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
1. `GET /api/v1/users/sessions/`: returns all active sessions for the authenticated user, indicating `is_current: true` for the session matching the caller's active session. Serialized responses MUST include `is_trusted: bool` and MUST NOT expose the raw `trust_hash`. The system MUST resolve the active session primarily using `session_id` from the authenticated access token (`request.auth`), falling back to the refresh cookie JTI.
2. `POST /api/v1/users/sessions/{id}/revoke/`: revokes a specific session. The system MUST mark `is_active=False` and immediately blacklist the session's tokens.
3. `POST /api/v1/users/sessions/revoke_others/`: revokes all active sessions belonging to the user except the caller's active session. The active session MUST be resolved primarily from the access token `session_id`, falling back to the refresh cookie JTI.
4. `POST /api/v1/users/sessions/trust_current/`: marks the caller's active session as trusted or untrusted based on `trust` payload. The active session MUST be resolved primarily from the access token `session_id`, falling back to the refresh cookie JTI.
5. `POST /api/v1/users/sessions/{id}/revoke_trust/`: revokes trust for a specific session. The system MUST set `trust_hash=None`, mark `is_active=False`, and atomically blacklist the session's tokens. If the session has a `trust_hash`, the system MUST also revoke and blacklist all active sibling sessions belonging to that user sharing the same `trust_hash`. If any revoked session matches the caller's current session, the system MUST clear `device_trust_token` and `refresh_token` cookies.
6. `POST /api/v1/users/sessions/revoke_trust_all/`: revokes trust for all sessions belonging to the user that are trusted (`trust_hash__isnull=False`). The system MUST clear `trust_hash=None`, mark `is_active=False`, blacklist their tokens, and delete the `device_trust_token` cookie.
7. `POST /api/v1/users/token/refresh/` (`CookieTokenRefreshView`): refreshes JWT tokens. The view MUST inspect the `refresh_token` HttpOnly cookie or the request JSON body (`refresh`). If neither is present, the request MUST be rejected with HTTP 401 Unauthorized (`Refresh token not found.`).
8. `GET /api/v1/users/sessions/devices/`: returns active user sessions aggregated by device identity. Trusted sessions are grouped by `trust_hash` and untrusted sessions are grouped by `(device_name, user_agent)`. Each aggregated device entry MUST include the most recent session `id`, `device_name`, latest `ip_address`, latest `last_activity`, `is_trusted`, `is_current` (if any session in the group is current), and `sessions_count`.

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

#### Scenario: Targeted device trust revocation terminates session and blacklists tokens
- GIVEN an active trusted session belonging to the authenticated user
- WHEN the user sends a `POST /api/v1/users/sessions/{id}/revoke_trust/` request
- THEN the system MUST set `trust_hash = None`
- AND the system MUST set `is_active = False`
- AND the system MUST blacklist both refresh and access tokens
- AND any subsequent attempt to refresh using that session's refresh token MUST be rejected.

#### Scenario: Global device trust revocation terminates all trusted sessions
- GIVEN an authenticated user with multiple active sessions, including trusted and untrusted sessions
- WHEN the user sends a `POST /api/v1/users/sessions/revoke_trust_all/` request
- THEN all sessions with active device trust MUST have `trust_hash = None` and `is_active = False`
- AND all their tokens MUST be blacklisted
- AND the response MUST delete the `device_trust_token` cookie.

#### Scenario: User session serialization exposes is_trusted boolean without leaking hash
- GIVEN an active session with an established `trust_hash`
- WHEN the user sends a `GET /api/v1/users/sessions/` request
- THEN the session representation MUST include `"is_trusted": true`
- AND the session representation MUST NOT contain `"trust_hash"`.

#### Scenario: List devices aggregates multiple sessions for the same physical device
- GIVEN an authenticated user with multiple active sessions sharing the same device trust token
- AND multiple active sessions sharing the same untrusted User-Agent
- WHEN the user sends a `GET /api/v1/users/sessions/devices/` request
- THEN the system MUST aggregate the sessions into single device entries
- AND the response MUST indicate the correct `sessions_count`, `is_trusted`, `is_current`, and most recent `last_activity`.

#### Scenario: Targeted device trust revocation cleans up sibling sessions sharing trust hash
- GIVEN an authenticated user with two active sessions sharing the same `trust_hash`
- WHEN the user revokes one of the sessions via `POST /api/v1/users/sessions/{id}/revoke_trust/`
- THEN both sessions sharing that `trust_hash` MUST be deactivated (`is_active = False`)
- AND both sessions MUST have their `trust_hash` cleared and tokens blacklisted.
