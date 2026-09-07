# Proposal: Support Technician Dispatch

## Why
Eliminate critical security vulnerabilities in the support system (lack of permission classes, un-scoped global querysets, missing tenant foreign keys) and implement the Hybrid Cross-Tenant Technician Dispatch model allowing master tenant technicians to service customer tenants safely.

## What Changes

## Scope
### In Scope
- **Support Multi-Tenancy**:
  - Link `Ticket` to `Tenant` (ForeignKey) and optional `Workspace` (ForeignKey).
  - Link `SupportMembership` to `Tenant` (or master tenant context).
  - Guard `TicketViewSet`, `CommentViewSet`, and related support views with `HasContextualPermission` and tenant-scoped querysets.
- **Hybrid Cross-Tenant Technician Dispatch**:
  - Default ticket-scoped access: technicians assigned to a ticket (`ticket.assigned_to`) can view, update, and resolve tickets across tenant boundaries without broad tenant membership.
  - Temporary diagnostic pass (`TechnicianAssignment`): formal TTL-bounded pass granting temporary diagnostic access to customer workspace/tenant, authorized by admin, with auto-expiration and audit logging.
  - Delegation endpoints: support managers in master tenant can assign/delegate tickets and issue diagnostic passes to technicians.
- **Backend Isolation**: Confined strictly to backend (`Monitor_Atlas`).

### Out of Scope
- Frontend UI modifications (`Monitor_Venus`).
- Non-support telemetry, alerts, or billing pipelines.

## Capabilities
### New Capabilities
- `support-multitenancy`: Scoped ticket and comment access control bound to active tenant and assigned technicians.
- `cross-tenant-technician-dispatch`: Hybrid model with default ticket-level delegation and TTL-bounded temporary diagnostic passes with audit logging.

### Modified Capabilities
- None

## Approach
- Add `tenant` (FK) and nullable `workspace` (FK) to `Ticket`, backfilling existing rows.
- Associate `SupportMembership` with `Tenant` context.
- Create `TechnicianAssignment` model tracking technician, tenant, workspace, TTL expiration, authorization status, and reason.
- Apply `HasContextualPermission` across support ViewSets; restrict `get_queryset()` to tickets belonging to active tenant or assigned to the authenticated technician.
- Enforce dynamic TTL expiration and audit logging for temporary diagnostic passes.
- Provide delegation actions on `TicketViewSet` for support managers.

## Affected Areas
- `Monitor_Atlas/support/models.py`
- `Monitor_Atlas/support/views.py`
- `Monitor_Atlas/support/serializers.py`
- `Monitor_Atlas/support/helpers.py`
- `Monitor_Atlas/support/urls.py`

## Risks
- **Cross-Tenant Data Exposure**: Querysets leaking foreign tickets. *Mitigation*: Strictly enforce active tenant or explicit assigned technician filtering.
- **Dangling Diagnostic Access**: Unexpired passes after ticket resolution. *Mitigation*: Enforce request-time TTL checks and auto-revocation on ticket closure.

## Rollback Plan
- Revert schema migrations via `python manage.py migrate support <prev_migration>`.
- Revert support app codebase changes via Git.

## Dependencies
- `roles.permissions.HasContextualPermission`
- `organizations.models.Tenant` and `organizations.models.Workspace`
- Django auditlog package

## Success Criteria
- Unauthorized or cross-tenant ticket requests return 401/403.
- Tickets and comments are strictly scoped to the active tenant.
- Assigned technicians can access and update their assigned cross-tenant tickets.
- Expired temporary diagnostic passes immediately deny workspace access.
- All technician assignments, delegations, and pass grants are logged to audit trail.
- Unit and integration tests pass without regression.
