## 1. Serializer & Model Enhancements

- [x] 1.1 Add `is_trusted` boolean property/method field to `UserSessionSerializer` and verify `trust_hash` is not in `fields`

## 2. Targeted & Global Revocation Endpoints

- [x] 2.1 Implement `POST /api/v1/users/sessions/{id}/revoke_trust/` action on `UserSessionViewSet` clearing `trust_hash`, terminating session, blacklisting tokens, and clearing cookies if current
- [x] 2.2 Implement `POST /api/v1/users/sessions/revoke_trust_all/` action on `UserSessionViewSet` terminating all trusted sessions, blacklisting tokens, clearing `trust_hash`, and deleting trust cookie
- [x] 2.3 Record audit log events for trust revocation actions

## 3. Automated Test Suite & Verification

- [x] 3.1 Add test verifying targeted device trust revocation clears `trust_hash`, deactivates session, and blacklists refresh token
- [x] 3.2 Add test verifying global device trust revocation invalidates all trusted sessions, blacklists tokens, and deletes trust cookie
- [x] 3.3 Add test verifying cross-user targeted trust revocation returns 404
- [x] 3.4 Add test verifying `UserSessionSerializer` outputs `is_trusted: bool` and does not leak `trust_hash`
- [x] 3.5 Run pytest suite against `Monitor_Atlas` and verify all tests pass
