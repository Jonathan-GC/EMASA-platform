# Feature: device-trust-revocation

## Objective
Implement targeted and global device trust revocation endpoints in `UserSessionViewSet` (`Monitor_Atlas`), ensuring revoking device trust strips the MFA bypass, terminates the active session, atomically blacklists tokens, clears trust cookies, and represents device trust as a boolean `is_trusted` in `UserSessionSerializer` without leaking the underlying trust hash.

## Problem & Why
Currently, while `trust_current` can toggle trust on the current session and `revoke` deactivates a session, there are no endpoints to:
1. Revoke trust for a specific remote device while invalidating its session and token family.
2. Revoke trust across all trusted devices for a user in bulk.
3. Obscure the cryptographic trust hash from API clients; `UserSessionSerializer` should explicitly present a clean `is_trusted: bool` flag and prevent `trust_hash` leakage.

## Scope
- In Scope:
  - OpenSpec lifecycle artifacts: `openspec/changes/device-trust-revocation/` (`proposal.md`, `design.md`, `specs/adaptive-auth-sessions/spec.md`, `tasks.md`).
  - `UserSessionSerializer`: Expose `is_trusted: bool` and keep `trust_hash` unexposed.
  - `UserSessionViewSet`: Add `revoke_trust` (`POST /api/v1/users/sessions/{id}/revoke_trust/`) and `revoke_trust_all` (`POST /api/v1/users/sessions/revoke_trust_all/`). Both terminate sessions, blacklist JWT token families, wipe `trust_hash`, and remove trust cookies if the current session is affected.
  - Comprehensive automated tests in `Monitor_Atlas/tests/test_adaptive_auth_sessions.py`.
  - OpenSpec validation and canonical spec update.
- Out of Scope:
  - Database schema alterations (existing `trust_hash` on `UserSession` is reused).
  - Frontend UI components in `Monitor_Venus`.

## Constraints & Delivery
- Delivery strategy: `ask-on-risk` (forecast ~200 lines < 400 lines).
- Engram mirror: Pending (Engram MCP unavailable in current session).
- Conventional commits: No AI attribution.

## Actionable Tasks

- [x] `TASK-1`: Author OpenSpec lifecycle artifacts (`proposal.md`, `design.md`, delta spec `specs/adaptive-auth-sessions/spec.md`, `tasks.md`) in `openspec/changes/device-trust-revocation/` and validate with OpenSpec CLI.
  - Route: Direct inline
  - Trigger evidence: OpenSpec documentation generation (<10k tokens)
  - Outcome: Validated via `openspec validate device-trust-revocation` (passed with code 0).
- [x] `TASK-2`: Author RED automated tests in `Monitor_Atlas/tests/test_adaptive_auth_sessions.py` covering targeted device trust revocation, global trust revocation, token blacklisting, cookie clearing, cross-user rejection, and `is_trusted` serialization.
  - Route: Delegated direct
  - Trigger evidence: Writer trigger (multi-file test harness expansion)
  - Outcome: Added 5 tests; observed RED (4 failures, 1 pre-existing 404).
- [x] `TASK-3`: Implement `is_trusted` boolean in `UserSessionSerializer` and `revoke_trust` / `revoke_trust_all` actions in `UserSessionViewSet` (`Monitor_Atlas/users/views.py`), turning tests GREEN.
  - Route: Delegated direct
  - Trigger evidence: Writer trigger (modifies `serializers.py` and `views.py`)
  - Outcome: Implemented serializer field and view actions; all 38 tests in `test_adaptive_auth_sessions.py` passed GREEN.
- [x] `TASK-4`: Execute verification suite, validate OpenSpec state, generate `verify-report.md`, archive change via `openspec archive`, and create work-unit commit.
  - Route: Direct inline
  - Trigger evidence: Test execution and verification reporting
  - Outcome: 38/38 tests passing, Django system check passed with 0 issues, change archived into `openspec/changes/archive/2026-10-12-device-trust-revocation/`, canonical spec updated.

## Verification Evidence
- `POSTGRES_HOST=127.0.0.1 venv/bin/pytest tests/test_adaptive_auth_sessions.py`: 38 passed, 1 warning in 33.20s.
- `POSTGRES_HOST=127.0.0.1 venv/bin/python manage.py check`: Passed with 0 issues.
- `openspec validate adaptive-auth-sessions`: Specification is valid.
- Work-Unit Commit: `a269907` (`feat(auth): add device trust revocation endpoints with session termination and hash secrecy`).

## Next Step
- Feature complete. Ready for PR/merge review per repository policy.
