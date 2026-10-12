# Proposal: Device-Centric Session Aggregation View

## Why

When users log into the application across multiple tabs, mobile web views, or app reloads, multiple `UserSession` records are spawned for the identical client device. The raw `GET /api/v1/users/sessions/` endpoint lists every individual session, cluttering the UI and presenting an abstraction leak to end-users who expect a consolidated "My Devices" list. A dedicated aggregation endpoint is needed to group sessions by physical/browser endpoint and enable atomic device revocation.

## What Changes

- Add `GET /api/v1/users/sessions/devices/` action on `UserSessionViewSet`:
  - Groups active sessions for the calling user by device identity:
    - Trusted sessions are grouped by `trust_hash`.
    - Untrusted sessions are grouped by `(device_name, user_agent)`.
  - Computes consolidated fields: primary `id` (most recent session), `device_name`, latest `ip_address`, latest `last_activity`, `is_trusted`, `is_current` (if any session in the group is current), and `sessions_count`.
- Update `revoke_trust`:
  - When revoking a trusted session, all active sibling sessions sharing that device's `trust_hash` are atomically terminated and blacklisted.

## Capabilities

### New Capabilities
<!-- None -->

### Modified Capabilities
- `adaptive-auth-sessions`: Support device-level aggregation of active user sessions and multi-session device trust revocation.

## Impact

- Affected Code: `Monitor_Atlas/users/views.py` (`UserSessionViewSet`)
- Affected Tests: `Monitor_Atlas/tests/test_adaptive_auth_sessions.py`
- APIs: `GET /api/v1/users/sessions/devices/`, `POST /api/v1/users/sessions/{id}/revoke_trust/`
