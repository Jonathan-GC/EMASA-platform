# Proposal: Capacitor Session Resolution and Hybrid Token Refresh

## Why

Mobile clients running under Ionic Capacitor (iOS WKWebView and Android WebView) cannot reliably maintain or send HttpOnly cookies due to cross-scheme and strict third-party cookie restrictions. Consequently, authenticated session management endpoints fail to identify the current session without cookies, and token refresh endpoints reject mobile requests that pass the refresh token in the JSON body.

## What Changes

- Authenticated session operations in `UserSessionViewSet` (`is_current`, `revoke_others`, `trust_current`) and `UserSessionSerializer` resolve the active session primarily from `request.auth` (`session_id` claim in the access token), falling back to the refresh cookie JTI.
- Add Capacitor/mobile request detection in `Monitor_Atlas` checking `X-Client-Platform: capacitor` and mobile origins (`capacitor://localhost`, `http://localhost`, `https://localhost`, `ionic://localhost`).
- Update `CookieTokenRefreshView` to accept `request.data.get("refresh")` when the HttpOnly cookie is absent **only** for verified Capacitor/mobile requests. Standard web browsers without cookies continue to be rejected with HTTP 401.

## Capabilities

### New Capabilities
<!-- None -->

### Modified Capabilities
- `adaptive-auth-sessions`: Enable access-token based session identification for active sessions and conditional body-based refresh token acceptance for Capacitor/mobile clients.

## Impact

- Affected Code:
  - `Monitor_Atlas/users/views.py`: `CookieTokenRefreshView`, `UserSessionViewSet`, session resolution helper.
  - `Monitor_Atlas/users/serializers.py`: `UserSessionSerializer.get_is_current`.
- Affected Tests:
  - `Monitor_Atlas/tests/test_adaptive_auth_sessions.py`.
