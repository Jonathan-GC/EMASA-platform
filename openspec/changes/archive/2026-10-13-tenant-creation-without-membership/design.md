# Design: Allow Tenant Creation for Users Without Tenant Membership

## Context

See [proposal.md](file:///home/weedopc/Projects/EMASA-platform/openspec/changes/tenant-creation-without-membership/proposal.md) for background and motivation.
`HasContextualPermission` ensures zero permission leakage across tenant and workspace boundaries. However, tenant creation is an exceptional operation: an onboarding user by definition has no tenant and cannot supply an `X-Tenant-ID` header.

## Goals / Non-Goals

**Goals:**
- Allow users with `user.tenant is None` and direct permission `organizations.add_tenant` to call `POST /api/v1/organizations/tenant/` successfully without an `X-Tenant-ID` header.
- Maintain strict tenant context enforcement for all other tenant operations (listing, retrieving, updating, deleting, or creating workspaces).
- Maintain strict isolation for users who already belong to a tenant.

**Non-Goals:**
- Allowing users who already belong to a tenant to create additional tenants without administrative privileges.
- Allowing unauthenticated users to create tenants.

## Decisions

### Decision 1: Scoped Exemption for Tenant Creation
- **Chosen**: In `HasContextualPermission.has_permission`, check if `scope == "tenant"` and `view.action == "create"` (or `request.method.lower() == "post"`) and `user.tenant is None`. If so, skip the `tenant is None` check.
- **Rationale**: This precisely targets initial tenant onboarding without relaxing tenant context enforcement for any existing tenant member or any other endpoint.

### Decision 2: Direct Model Permission Fallback in `has_contextual_perm`
- **Chosen**: When `tenant is None and workspace is None`, inspect `user.user_permissions` and `user.has_perm(codename)` instead of immediately returning `False`.
- **Rationale**: Model-level permissions assigned directly to users (via `assign_perm("organizations.add_tenant", user)`) represent non-contextual, global capabilities.

## Risks / Trade-offs

- **[Risk] Unintended global permission execution**: A user might bypass contextual isolation if permissions leak when context is None.
  - *Mitigation*: Direct permission evaluation is only reached if neither workspace nor tenant is resolvable, and viewsets enforcing `WORKSPACE_SCOPED_MODELS` and `TENANT_SCOPED_MODELS` already reject unresolvable contexts before reaching this fallback.

## Migration Plan

No database migrations or deployment steps required.
