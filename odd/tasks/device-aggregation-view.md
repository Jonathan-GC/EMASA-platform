# Feature: device-aggregation-view

## Objective
Provide a device-centric aggregation endpoint `GET /api/v1/users/sessions/devices/` in `UserSessionViewSet` (`Monitor_Atlas`) that deduplicates multiple active sessions originating from the same physical/browser device, and ensure targeted device trust revocation cleans up all active sibling sessions sharing that device's `trust_hash`.

## Problem & Why
Currently, users with multiple open tabs or browser sessions see redundant entries in their active session list for the same physical device. Frontend requires a clean "My Devices" view where sessions are consolidated per device endpoint with session counts and unified device revocation.

## Scope
- In Scope:
  - OpenSpec lifecycle artifacts in `openspec/changes/device-aggregation-view/`.
  - Endpoint `GET /api/v1/users/sessions/devices/` on `UserSessionViewSet` grouping active sessions by `trust_hash` (for trusted devices) and `(device_name, user_agent)` (for untrusted devices).
  - Updated `revoke_trust` to terminate all active sessions sharing the target device's `trust_hash`.
  - Automated tests in `Monitor_Atlas/tests/test_adaptive_auth_sessions.py`.
  - Canonical specification update and OpenSpec archive.
- Out of Scope:
  - Database schema changes (aggregation performed dynamically over `UserSession`).
  - Frontend Vue components in `Monitor_Venus`.

## Constraints & Delivery
- Delivery strategy: `ask-on-risk` (forecast ~180 lines < 400 lines).
- Engram mirror: Pending (Engram MCP unavailable in current session).
- Conventional commits: No AI attribution.

## Actionable Tasks

- [x] `TASK-1`: Author OpenSpec lifecycle artifacts (`proposal.md`, `design.md`, delta spec `specs/adaptive-auth-sessions/spec.md`, `tasks.md`) in `openspec/changes/device-aggregation-view/` and validate with OpenSpec CLI.
  - Route: Direct inline
  - Trigger evidence: OpenSpec documentation generation (<10k tokens)
  - Outcome: Validated via `openspec validate device-aggregation-view` (passed with code 0).
- [x] `TASK-2`: Author RED automated tests in `Monitor_Atlas/tests/test_adaptive_auth_sessions.py` covering device aggregation (trusted grouping, untrusted grouping, `sessions_count`, `is_current`) and sibling session cleanup on `revoke_trust`.
  - Route: Delegated direct
  - Trigger evidence: Writer trigger (multi-file changes across tests and views)
  - Outcome: Observed RED failure on `test_user_session_devices_aggregation` (404 != 200) and `test_user_session_revoke_trust_cleans_up_sibling_sessions` (sibling session trust hash not cleared).
- [x] `TASK-3`: Implement `devices` action and sibling cleanup in `UserSessionViewSet` (`Monitor_Atlas/users/views.py`), turning tests GREEN.
  - Route: Delegated direct
  - Trigger evidence: Writer trigger (views and tests)
  - Outcome: Implemented `devices` action aggregating sessions by `trust_hash` or `(device_name, user_agent)` and updated `revoke_trust` to clean up all sibling sessions sharing `trust_hash`. All 40 tests passed GREEN.
- [x] `TASK-4`: Execute verification suite, validate OpenSpec state, generate `verify-report.md`, archive change via `openspec archive`, and create work-unit commit.
  - Route: Direct inline
  - Trigger evidence: Test execution and verification reporting
  - Outcome: 40/40 tests passing in pytest, Django system check passed with 0 issues, change archived into `openspec/changes/archive/2026-10-12-device-aggregation-view/`, canonical spec updated.

## Verification Evidence
- Observed RED:
  - `AdaptiveAuthSessionsTests.test_user_session_devices_aggregation` failed with `AssertionError: 404 != 200`
  - `AdaptiveAuthSessionsTests.test_user_session_revoke_trust_cleans_up_sibling_sessions` failed with `AssertionError: 'shared_hash_beta' is not None`
- Observed GREEN:
  - `POSTGRES_HOST=127.0.0.1 venv/bin/pytest tests/test_adaptive_auth_sessions.py -k "devices_aggregation or cleans_up_sibling"` -> 2 passed in 3.47s
  - `POSTGRES_HOST=127.0.0.1 venv/bin/pytest tests/test_adaptive_auth_sessions.py` -> 40 passed in 34.45s
- Django system check: `venv/bin/python manage.py check` -> 0 issues identified.
- OpenSpec: Canonical specification `adaptive-auth-sessions` validated with code 0.
- Work-Unit Commit: `0ca12eb` (`feat(auth): add device session aggregation and sibling trust revocation`).

## Next Step
- Feature complete. Ready for PR/merge review per repository policy.

