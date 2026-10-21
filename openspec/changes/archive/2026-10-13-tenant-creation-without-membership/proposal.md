# Proposal: Allow Tenant Creation for Users Without Tenant Membership

## Why

When an onboarding user registers without an initial tenant, `assign_new_user_base_permissions` assigns them the `organizations.add_tenant` model permission so they can create their organization. However, `HasContextualPermission` marks `scope = "tenant"` as requiring an active tenant context, unconditionally rejecting requests with `PermissionDenied("Active tenant context is required for this operation.")` if `tenant is None`. Furthermore, `has_contextual_perm` fails to check direct user permissions when neither workspace nor tenant context exists. This creates a circular dependency blocking initial tenant onboarding.

## What Changes

- Update `HasContextualPermission.has_permission` in `Monitor_Atlas/roles/permissions.py`:
  - When `scope == "tenant"` and action is `create` (`POST`) and `user.tenant is None`, bypass the mandatory `tenant is None` check.
- Update `has_contextual_perm` in `Monitor_Atlas/roles/permissions.py`:
  - When both `workspace is None` and `tenant is None`, evaluate direct model permissions on the user (`user.user_permissions` and `user.has_perm`).

## Capabilities

### New Capabilities
<!-- None -->

### Modified Capabilities
- `contextual-authorization`: Permit initial tenant creation by tenant-less users possessing `organizations.add_tenant` without demanding an active tenant context.

## Impact

- Affected Code: `Monitor_Atlas/roles/permissions.py`
- Affected Tests: `Monitor_Atlas/tests/test_contextual_permissions.py`
- APIs: `POST /api/v1/organizations/tenant/`
