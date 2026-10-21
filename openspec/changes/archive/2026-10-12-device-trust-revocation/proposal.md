# Proposal: Device Trust Revocation and Hash Secrecy

## Why

Currently, when a device is compromised, lost, or decommissioned, users have no dedicated API to revoke trust for that specific device while terminating its active session and blacklisting its token family. Furthermore, there is no bulk endpoint to revoke trust across all devices for an account. Lastly, `UserSessionSerializer` must ensure the raw cryptographic trust hash is never exposed to API consumers, presenting a clean boolean `is_trusted` flag instead.

## What Changes

- Add targeted device trust revocation action to `UserSessionViewSet`:
  - `POST /api/v1/users/sessions/{id}/revoke_trust/`: Clears `trust_hash = None`, sets `is_active = False`, atomically blacklists `refresh_token_jti` and `access_token_jti`, deletes `device_trust_token` and `refresh_token` cookies if targeting the caller's session, and writes an audit log entry.
- Add bulk device trust revocation action to `UserSessionViewSet`:
  - `POST /api/v1/users/sessions/revoke_trust_all/`: Revokes trust across all sessions belonging to the authenticated user that possess a `trust_hash` (or all sessions), sets `trust_hash = None`, terminates them (`is_active = False`), blacklists their token families, and deletes the `device_trust_token` cookie.
- Update `UserSessionSerializer` in `Monitor_Atlas/users/serializers.py`:
  - Expose `is_trusted: bool` computed dynamically.
  - Ensure the internal `trust_hash` column is not exposed in serialized responses.

## Capabilities

### New Capabilities
<!-- None -->

### Modified Capabilities
- `adaptive-auth-sessions`: Support targeted and global device trust revocation with session deactivation, token blacklisting, cookie invalidation, and hash confidentiality.

## Impact

- Affected Code: `Monitor_Atlas/users/serializers.py` (`UserSessionSerializer`), `Monitor_Atlas/users/views.py` (`UserSessionViewSet`)
- Affected Tests: `Monitor_Atlas/tests/test_adaptive_auth_sessions.py`
- APIs: `POST /api/v1/users/sessions/{id}/revoke_trust/`, `POST /api/v1/users/sessions/revoke_trust_all/`, `GET /api/v1/users/sessions/`
