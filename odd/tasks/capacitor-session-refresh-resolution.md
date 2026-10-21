# Feature: capacitor-session-refresh-resolution

## Objective
Support robust session resolution and token refresh for mobile/Capacitor clients in `Monitor_Atlas`. Authenticated session operations prioritize resolving the current active session via `request.auth` (`session_id`) from the access token, with cookie JTI as fallback. The `CookieTokenRefreshView` allows reading `request.data.get("refresh")` when the HttpOnly cookie is absent only if the request originates from Capacitor/mobile (via `X-Client-Platform: capacitor` or mobile origin).

## Problem & Why
Capacitor webviews (iOS WKWebView / Android WebView) face strict cross-origin cookie restrictions that prevent reliable HttpOnly cookie storage and transmission. In `UserSessionViewSet` (`is_current`, `revoke_others`, `trust_current`), relying solely on `request.COOKIES` breaks mobile session resolution, causing all sessions to appear non-current and `revoke_others` to inadvertently revoke the active device session. In `CookieTokenRefreshView`, omitting the cookie causes immediate 401 failure, ignoring the refresh token sent in the body.

## Scope
- In Scope:
  - OpenSpec lifecycle artifacts: `proposal.md`, `design.md`, `specs/adaptive-auth-sessions/spec.md`, `tasks.md`.
  - Session resolution helper in `Monitor_Atlas/users/views.py` and `UserSessionSerializer` in `Monitor_Atlas/users/serializers.py` prioritizing `request.auth.payload.get("session_id")` over refresh cookies.
  - Capacitor detection utility (`is_capacitor_request`) checking `X-Client-Platform: capacitor` header and `Origin` (`capacitor://localhost`, `http://localhost`, `https://localhost`, `ionic://localhost`).
  - Update `CookieTokenRefreshView` to permit body refresh tokens when cookie is missing for Capacitor clients; continue enforcing cookies for standard web clients.
  - Comprehensive unit/integration tests in `Monitor_Atlas/tests/test_adaptive_auth_sessions.py`.
- Out of Scope:
  - Frontend Vue modifications (frontend already sends body fallback).
  - Database schema alterations.

## Constraints & Delivery
- Delivery strategy: `ask-on-risk` (forecast < 400 lines).
- Engram mirror: Pending (Engram MCP unavailable in current session).
- Conventional commits: No AI attribution.

## Actionable Tasks

- [x] `TASK-1`: Author OpenSpec lifecycle artifacts (`proposal.md`, `design.md`, delta spec `specs/adaptive-auth-sessions/spec.md`, `tasks.md`) and validate with OpenSpec CLI.
  - Route: Direct inline
  - Trigger evidence: OpenSpec documentation generation (<10k tokens)
  - Outcome: Validated via `openspec validate capacitor-session-refresh-resolution` (4/4 complete)
- [x] `TASK-2`: Implement session resolution helper in `Monitor_Atlas/users/views.py` and update `UserSessionSerializer`, `revoke_others`, and `trust_current` to resolve session from `request.auth` (`session_id`) with cookie fallback.
  - Route: Delegated direct
  - Trigger evidence: Multi-file implementation touching views, serializers, and tests
  - Outcome: Implemented `get_current_session_for_request(request)`; updated `UserSessionSerializer` and `UserSessionViewSet` actions.
- [x] `TASK-3`: Implement Capacitor request detection and update `CookieTokenRefreshView` to accept `request.data["refresh"]` when cookie is missing only for Capacitor/mobile clients.
  - Route: Delegated direct (alongside Task 2)
  - Trigger evidence: Multi-file implementation
  - Outcome: Implemented `is_capacitor_request(request)`; updated `CookieTokenRefreshView.post` to accept body refresh conditionally.
- [x] `TASK-4`: Expand test suite in `Monitor_Atlas/tests/test_adaptive_auth_sessions.py` covering Bearer-only session identification, Capacitor body refresh, and web cookie enforcement.
  - Route: Delegated direct (alongside Task 2)
  - Trigger evidence: Multi-file verification
  - Outcome: Added 6 new test cases; 32/32 tests passing.
- [x] `TASK-5`: Run full test suite, generate OpenSpec `verify-report.md`, archive OpenSpec change, and create conventional work-unit commit.
  - Route: Direct inline
  - Trigger evidence: Verification and archive reporting
  - Outcome: Verified 32/32 tests (`28.16s`), generated `verify-report.md`, archived change via `openspec archive --yes capacitor-session-refresh-resolution`.

## Verification Evidence
- `TASK-1`: `openspec validate capacitor-session-refresh-resolution` passed with code 0.
- `TASK-2`, `TASK-3`, & `TASK-4`: Implementation verified across 32 unit and integration tests.
- `TASK-5`: Pytest suite passed (`32 passed, 1 warning in 28.16s`). Change archived cleanly into `openspec/changes/archive/2026-10-08-capacitor-session-refresh-resolution/`.
- Work-Unit Commit: `220cdd0` (`feat(auth): resolve session via access token and guard body refresh for capacitor`)

## Next Step
- Complete. Feature ready for push/PR per repository policy.
