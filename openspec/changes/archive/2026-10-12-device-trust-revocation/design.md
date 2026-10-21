# Design: Device Trust Revocation and Hash Secrecy

## Context

See [proposal.md](file:///home/weedopc/Projects/EMASA-platform/openspec/changes/device-trust-revocation/proposal.md) for background and motivation.
In `Monitor_Atlas`, `UserSession` records track client sessions, JWT token identifiers (`refresh_token_jti`, `access_token_jti`), and optional device trust associations (`trust_hash`).
When a device's trust is revoked, zero-trust security demands that:
1. The trust association is stripped immediately (`trust_hash = None`), preventing future 2FA bypass from that hardware.
2. Any active in-flight session on that device is immediately terminated (`is_active = False`) and its JWT tokens blacklisted.
3. Relevant trust and refresh cookies are purged from the browser when the revocation targets the caller's session.
4. Serialized representations must never leak raw cryptographic digests (`trust_hash`), exposing only an `is_trusted: bool` status.

## Goals / Non-Goals

**Goals:**
- Provide `POST /api/v1/users/sessions/{id}/revoke_trust/` to revoke trust and terminate the target session owned by the authenticated user.
- Provide `POST /api/v1/users/sessions/revoke_trust_all/` to revoke trust and terminate all trusted sessions for the authenticated user in bulk.
- Clear `trust_hash`, set `is_active = False`, and blacklist `refresh_token_jti` and `access_token_jti`.
- Expire `device_trust_token` cookies in HTTP response when revoking the caller's session or when calling bulk revocation.
- Add `is_trusted` field to `UserSessionSerializer` indicating if a session is currently trusted, without exposing `trust_hash`.
- Prevent cross-user revocation with `404 Not Found`.

**Non-Goals:**
- Altering underlying database schemas or migrations.
- Altering the scoring weights in `AdaptiveTrustEngine`.

## Decisions

### Decision 1: Combined Trust Revocation and Session Invalidation
- **Chosen**: Revoking device trust atomically sets `trust_hash = None`, sets `is_active = False`, and calls `_blacklist_session_tokens(session)`.
- **Rationale**: If a device's trust is revoked (e.g. lost device, suspected intrusion), allowing active tokens to remain valid would pose an immediate risk. Immediate invalidation enforces a strict zero-trust posture.

### Decision 2: Hash Secrecy in Serializer
- **Chosen**: In `UserSessionSerializer`, add `is_trusted = serializers.SerializerMethodField()`. Do not include `trust_hash` in `fields`.
- **Rationale**: Cryptographic digests and tokens should never be exposed over the wire if a simple boolean satisfies client presentation requirements.

## Risks / Trade-offs

- **[Risk] Current Session Invalidation**: If the user revokes trust on their *own* current device via targeted endpoint or bulk endpoint, their current session is terminated.
  - *Mitigation*: The response clears both `device_trust_token` and `refresh_token` cookies. The client will receive `200 OK` and subsequent requests will require re-authentication.

## Migration Plan

No database migrations or deployment steps required. The change utilizes existing fields on `UserSession` and adds DRF actions and serializer fields.
