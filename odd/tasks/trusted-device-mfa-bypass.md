# Feature: trusted-device-mfa-bypass

## Objective
Update the `AdaptiveTrustEngine` in `Monitor_Atlas` so that a user possessing an active, valid trusted device cookie (`device_trust_token`) directly bypasses the MFA challenge, unless the tenant security level is set to `HIGH` or a critical threat anomaly (`impossible_travel` or `suspicious_ip`/`threat_detected`) is present.

## Problem & Why
Currently, a valid trusted device cookie awards only +40 heuristic points. In tenants configured with the default `MEDIUM` security tier (threshold 75), trusted users logging in from dynamic IP addresses or roaming networks fail the threshold (scoring 50-65) and are forced to perform MFA repeatedly, negating the purpose of trusting a device.

## Scope
- In Scope:
  - OpenSpec lifecycle artifacts: `proposal.md`, `design.md`, `specs/adaptive-auth-sessions/spec.md`, `tasks.md`.
  - Update `AdaptiveTrustEngine.evaluate` to elevate valid device trust to direct MFA bypass when no critical threat is present and tenant security tier is not `HIGH`.
  - Retain strict enforcement on `HIGH` tenant security level (no bypass).
  - Retain strict enforcement when critical threats (`HTTP_X_IMPOSSIBLE_TRAVEL`, `HTTP_X_SUSPICIOUS_IP`, `HTTP_X_THREAT_DETECTED`) are detected.
  - Test suite expansion in `Monitor_Atlas/tests/test_adaptive_auth_sessions.py`.
  - OpenSpec verification report and validation.
- Out of Scope:
  - Database schema changes (existing models and fields remain unchanged).
  - Frontend UI modifications in `Monitor_Venus`.

## Constraints & Delivery
- Delivery strategy: `ask-on-risk` (forecast < 400 lines).
- Engram mirror: Pending (Engram MCP unavailable in current session).
- Conventional commits: No AI attribution.

## Actionable Tasks

- [x] `TASK-1`: Author OpenSpec lifecycle artifacts (`proposal.md`, `design.md`, delta spec `specs/adaptive-auth-sessions/spec.md`, `tasks.md`) and validate with OpenSpec CLI.
  - Route: Direct inline
  - Trigger evidence: OpenSpec documentation generation (<10k tokens)
  - Outcome: Validated via `openspec validate trusted-device-mfa-bypass` (4/4 complete)
- [x] `TASK-2`: Refactor `AdaptiveTrustEngine.evaluate` in `Monitor_Atlas/users/trust_engine.py` to allow direct bypass for trusted devices while strictly enforcing MFA under critical threats or `HIGH` tenant security tier.
  - Route: Delegated direct
  - Trigger evidence: Multi-file implementation touching core auth logic and tests
  - Outcome: Direct bypass enabled for verified trusted devices; strict MFA enforced for HIGH tier and critical threats (`is_impossible_travel`, `is_suspicious_ip`).
- [x] `TASK-3`: Expand automated test suite in `Monitor_Atlas/tests/test_adaptive_auth_sessions.py` covering trusted device roaming bypass, threat detection overrides, and `HIGH` tier strictness.
  - Route: Delegated direct (alongside Task 2)
  - Trigger evidence: Multi-file verification
  - Outcome: 3 new test cases added; 26/26 tests passing in `venv/bin/pytest tests/test_adaptive_auth_sessions.py`.
- [x] `TASK-4`: Execute verification suite, generate OpenSpec `verify-report.md`, validate OpenSpec state, and create work-unit commit.
  - Route: Direct inline
  - Trigger evidence: Test suite execution and verification reporting
  - Outcome: Verified 26/26 tests, generated `verify-report.md`, archived change via `openspec archive --yes trusted-device-mfa-bypass`, updating canonical spec in `openspec/specs/adaptive-auth-sessions/spec.md`.

## Verification Evidence
- `TASK-1`: `openspec validate trusted-device-mfa-bypass` passed with code 0.
- `TASK-2` & `TASK-3`: Refactored `AdaptiveTrustEngine.evaluate` and verified with 26 unit and integration tests.
- `TASK-4`: Full pytest suite passed (`26 passed, 1 warning in 23.56s`). Change archived cleanly into `openspec/changes/archive/2026-10-08-trusted-device-mfa-bypass/`.
- Work-Unit Commit: `7930826` (`feat(auth): bypass MFA on trusted devices unless critical threat or HIGH security tier`)

## Next Step
- Complete. Feature ready for push/PR per repository policy.
