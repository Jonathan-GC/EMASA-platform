# Design: Device-Centric Session Aggregation View

## Context

See [proposal.md](file:///home/weedopc/Projects/EMASA-platform/openspec/changes/device-aggregation-view/proposal.md) for background.
Currently, each browser tab or refresh can produce a distinct `UserSession` row. To present a coherent "Connected Devices" UI, the backend aggregates these sessions dynamically without adding table overhead.

## Goals / Non-Goals

**Goals:**
- Provide `GET /api/v1/users/sessions/devices/` returning aggregated device representations.
- Group trusted sessions by `trust_hash` and untrusted sessions by `(device_name, user_agent)`.
- Include `sessions_count`, latest `ip_address`, latest `last_activity`, `is_trusted`, `is_current`, and the representative `id`.
- Ensure `revoke_trust` cleans up all sibling sessions sharing the device's `trust_hash`.

**Non-Goals:**
- Creating a separate persistent `Device` database model.
- Breaking existing raw `GET /api/v1/users/sessions/` behavior.

## Decisions

### Decision 1: Dynamic In-Memory Aggregation vs. Database Table
- **Chosen**: Query user's active sessions ordered by `-last_activity` and group in-memory.
- **Rationale**: User session counts per user are small (typically < 20). Performing in-memory aggregation avoids schema migrations, keeps the system lightweight, and guarantees real-time consistency with active tokens.

### Decision 2: Grouping Heuristic
- **Chosen**: If `trust_hash` is present, group by `f"trust:{trust_hash}"`. If absent, group by `f"ua:{device_name}::{user_agent}"`.
- **Rationale**: Trusted devices are cryptographically bound to a single trust token cookie. Untrusted devices share consistent platform user-agents and device names.

## Risks / Trade-offs

- **[Risk] Untrusted NAT/IP Drift**: Multiple untrusted devices with identical User-Agents could group together.
  - *Mitigation*: For enterprise platforms, browser User-Agent + parsed OS/device name is standard heuristic. Encouraging device trust solves ambiguity via cryptographic cookies.

## Migration Plan

No database migrations or deployment steps required.
