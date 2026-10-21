# Feature: Token Family Session Management & Device Trust Controls

## Objective
Extend user session management and SimpleJWT blacklisting in Monitor_Atlas so that revoking a session atomically invalidates the entire token family (both access token and refresh token), provide an endpoint to revoke all active sessions, and add an on-demand device trust action (`trust_current`) on `UserSessionViewSet`.

## Scope & Constraints
- Add `access_token_jti` to `UserSession` model.
- Implement `SessionAccessToken` subclassing `(BlacklistMixin, AccessToken)` with session liveness checks.
- Register `SessionAccessToken` in `SIMPLE_JWT["AUTH_TOKEN_CLASSES"]` and hook into `RefreshToken.access_token_class`.
- Update login, 2FA, and token refresh to bind `session_id` into access/refresh tokens and persist current `access_token_jti`.
- Update `UserSessionViewSet.revoke` and `revoke_others` to blacklist both refresh and access tokens in `BlacklistedToken`.
- Add `UserSessionViewSet.revoke_all` to terminate and blacklist all user sessions.
- Add `UserSessionViewSet.trust_current` to dynamically toggle device trust status for the current session.
- Add automated unit and integration tests covering token family blacklisting, access token rejection on revoked sessions, `revoke_all`, and `trust_current`.
- Zero changes in `Monitor_Venus`.

## Implementation Tasks
- [x] Task 1: Add `access_token_jti` to `UserSession` in `Monitor_Atlas/users/models.py` and execute migration.
- [x] Task 2: Implement `SessionAccessToken` in `Monitor_Atlas/users/tokens.py`, configure `settings.py` and hook `RefreshToken.access_token_class`.
- [x] Task 3: Update token issuance and refresh workflows in `Monitor_Atlas/users/views.py` (`CookieTokenObtainPairView`, `UserTwoFactorVerifyView`, `CookieTokenRefreshView`).
- [x] Task 4: Update `UserSessionViewSet` in `Monitor_Atlas/users/views.py` with full-family blacklisting (`revoke`, `revoke_others`) and new actions (`revoke_all`, `trust_current`).
- [x] Task 5: Implement automated verification tests in `Monitor_Atlas/tests/test_adaptive_auth_sessions.py` and verify all tests pass.

