# Design: Capacitor Session Resolution and Hybrid Token Refresh

## Context

See [proposal.md](file:///home/weedopc/Projects/EMASA-platform/openspec/changes/capacitor-session-refresh-resolution/proposal.md).
In `Monitor_Atlas`, session endpoints in `UserSessionViewSet` rely on `request.COOKIES.get(REFRESH_COOKIE_NAME)` to resolve the active device session, while `CookieTokenRefreshView` requires the refresh token to be in an HttpOnly cookie. In Capacitor/mobile apps, cookies are either not shared across origins or blocked, leading to failed session operations and broken token refreshes.

## Goals / Non-Goals

**Goals:**
- Enable resolution of the current session in `UserSessionViewSet` (`is_current`, `revoke_others`, `trust_current`) via `request.auth` (`session_id`), falling back to cookie JTI.
- Add utility `is_capacitor_request(request)` detecting mobile requests via `X-Client-Platform: capacitor` or origins (`capacitor://localhost`, `http://localhost`, `https://localhost`, `ionic://localhost`).
- Allow `CookieTokenRefreshView` to accept `request.data.get("refresh")` when cookie is missing for Capacitor clients, preserving cookie enforcement for desktop web browsers.

**Non-Goals:**
- Changing token lifetimes or encryption algorithms.
- Modifying frontend client storage mechanisms.

## Decisions

### Decision 1: Access Token Primary Session Resolution
- **Chosen**: In authenticated requests, inspect `request.auth` (which is an instance of `SessionAccessToken`). If `request.auth` has `session_id`, resolve the active session directly by `id=session_id`. If absent or not authenticated, fall back to checking `request.COOKIES.get(REFRESH_COOKIE_NAME)`.
- **Rationale**: The access token is what cryptographically authenticates the HTTP request. Its claims already include `session_id`. This provides an immediate $O(1)$ lookup and removes all cookie dependency from mobile clients.

### Decision 2: Guarded Body Refresh Fallback
- **Chosen**: In `CookieTokenRefreshView`, if `request.COOKIES.get(REFRESH_COOKIE_NAME)` is absent, check `is_capacitor_request(request)`. If true, read `request.data.get("refresh")`. If false, reject with 401.
- **Rationale**: Desktop web clients must continue to use HttpOnly cookies to protect against XSS token exfiltration. Allowing body tokens only for Capacitor requests provides the required mobile compatibility without degrading web security.

## Risks / Trade-offs

- **[Risk] Origin spoofing outside browser**: Non-browser clients (curl) can pass `X-Client-Platform: capacitor` or custom origin.
  - *Mitigation*: Refresh tokens are already cryptographically signed and tracked in the database. HttpOnly cookies exist specifically to defend against in-browser XSS, where the `Origin` header cannot be spoofed by browser JavaScript.

## Migration Plan

Zero database migrations required. Backend changes are backwards-compatible with existing web clients.
