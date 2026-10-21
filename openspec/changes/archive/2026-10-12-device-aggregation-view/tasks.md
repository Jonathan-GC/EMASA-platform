## 1. Automated Test Suite (RED)

- [x] 1.1 Add test verifying `GET /api/v1/users/sessions/devices/` aggregates trusted sessions by `trust_hash` with correct `sessions_count`, `is_trusted=True`, and `is_current`
- [x] 1.2 Add test verifying `GET /api/v1/users/sessions/devices/` aggregates untrusted sessions by `(device_name, user_agent)`
- [x] 1.3 Add test verifying `revoke_trust` terminates and blacklists all sibling sessions sharing the target device's `trust_hash`

## 2. Implementation (GREEN)

- [x] 2.1 Implement `@action(detail=False, methods=["get"]) def devices` in `UserSessionViewSet` (`Monitor_Atlas/users/views.py`) with OpenAPI schema
- [x] 2.2 Update `revoke_trust` action in `UserSessionViewSet` to clean up all active sibling sessions for `request.user` sharing `session.trust_hash`

## 3. Verification & Governance

- [x] 3.1 Run pytest test suite `tests/test_adaptive_auth_sessions.py` to confirm all tests pass
- [ ] 3.2 Validate OpenSpec state, generate `verify-report.md`, and archive change

