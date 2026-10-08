## 1. Session Resolution Refactoring

- [x] 1.1 Implement `get_current_session_for_request(request)` helper in `Monitor_Atlas/users/views.py` resolving via `request.auth` (`session_id`) then cookie JTI
- [x] 1.2 Update `UserSessionSerializer` and `UserSessionViewSet.get_serializer_context` to use access token `session_id` as primary identifier for `is_current`
- [x] 1.3 Update `UserSessionViewSet.revoke_others` and `UserSessionViewSet.trust_current` to resolve active session via the helper

## 2. Guarded Token Refresh Implementation

- [x] 2.1 Implement `is_capacitor_request(request)` utility checking `X-Client-Platform: capacitor` and mobile origins
- [x] 2.2 Update `CookieTokenRefreshView` to accept `request.data.get("refresh")` when cookie is absent only for Capacitor requests, returning 401 for web clients

## 3. Test Suite Expansion & Verification

- [x] 3.1 Add unit test verifying `UserSessionViewSet` marks `is_current: true` via Bearer token without cookies
- [x] 3.2 Add unit test verifying `revoke_others` and `trust_current` succeed via Bearer token without cookies
- [x] 3.3 Add unit test verifying `CookieTokenRefreshView` accepts body refresh token with `X-Client-Platform: capacitor`
- [x] 3.4 Add unit test verifying `CookieTokenRefreshView` rejects body refresh token from standard web origin without cookie
- [x] 3.5 Run full test suite in `tests/test_adaptive_auth_sessions.py` to ensure zero regressions
