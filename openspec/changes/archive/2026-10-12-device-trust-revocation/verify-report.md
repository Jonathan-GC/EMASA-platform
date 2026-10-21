```yaml
schema: gentle-ai.verify-result/v1
evidence_revision: current
verdict: pass
blockers: 0
critical_findings: 0
requirements: 1/1
scenarios: 3/3
test_command: POSTGRES_HOST=127.0.0.1 venv/bin/pytest tests/test_adaptive_auth_sessions.py
test_exit_code: 0
build_command: POSTGRES_HOST=127.0.0.1 venv/bin/python manage.py check
build_exit_code: 0
```

## Verification Report
**Change**: device-trust-revocation
**Version**: 1.0.0
**Mode**: Standard

### Completeness
| Metric | Value |
|--------|-------|
| Tasks total | 6 |
| Tasks complete | 6 |
| Tasks incomplete | 0 |

### Build & Tests Execution
**Build**: Passed
```text
venv/bin/python manage.py check
System check identified no issues (0 silenced).
```

**Tests**: 38 passed / 0 failed / 0 skipped
```text
POSTGRES_HOST=127.0.0.1 venv/bin/pytest tests/test_adaptive_auth_sessions.py
======================== 38 passed, 1 warning in 33.20s ========================
```

### Spec Compliance Matrix
| Requirement | Scenario | Test | Result |
|-------------|----------|------|--------|
| Active User Session Tracking and Remote Revocation | Targeted device trust revocation terminates session and blacklists tokens | `test_user_session_targeted_revoke_trust`, `test_user_session_targeted_revoke_trust_current_clears_cookies` | COMPLIANT |
| Active User Session Tracking and Remote Revocation | Global device trust revocation terminates all trusted sessions | `test_user_session_revoke_trust_all` | COMPLIANT |
| Active User Session Tracking and Remote Revocation | User session serialization exposes is_trusted boolean without leaking hash | `test_user_session_serializer_exposes_is_trusted_and_hides_trust_hash` | COMPLIANT |

**Compliance summary**: 3/3 scenarios compliant

### Correctness (Static Evidence)
| Requirement | Status | Notes |
|------------|--------|-------|
| Targeted Trust & Session Revocation | Implemented | `UserSessionViewSet.revoke_trust` clears `trust_hash`, sets `is_active=False`, blacklists token family, and clears cookies if targeting caller's session. |
| Global Trust & Session Revocation | Implemented | `UserSessionViewSet.revoke_trust_all` clears `trust_hash`, marks all trusted sessions inactive, blacklists tokens, and deletes trust cookie. |
| Hash Confidentiality & Boolean Presentation | Implemented | `UserSessionSerializer` exposes `is_trusted: bool` and does not include `trust_hash` in `fields`. |
