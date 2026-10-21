# Feature: tenant-creation-without-membership

## Objective
Allow users without an existing tenant membership (`user.tenant is None`) who possess the `organizations.add_tenant` permission to create a new tenant via `POST /api/v1/organizations/tenant/` without requiring an active tenant context or `X-Tenant-ID` header.

## Problem & Why
Currently, `HasContextualPermission` categorizes `scope = "tenant"` under `TENANT_SCOPED_MODELS` and unconditionally blocks requests when `tenant is None` with `PermissionDenied("Active tenant context is required for this operation.")`. Furthermore, `has_contextual_perm` fails to evaluate direct model permissions when neither workspace nor tenant context exists. This creates a circular dependency preventing new onboarding users from creating their initial tenant.

## Scope
- In Scope:
  - OpenSpec lifecycle artifacts in `openspec/changes/tenant-creation-without-membership/`.
  - Update `HasContextualPermission.has_permission` in `Monitor_Atlas/roles/permissions.py` to exempt tenant creation when `user.tenant is None`.
  - Update `has_contextual_perm` in `Monitor_Atlas/roles/permissions.py` to evaluate direct user permissions when no context exists.
  - Automated tests in `Monitor_Atlas/tests/test_contextual_permissions.py`.
  - OpenSpec validation, canonical spec update, and full regression verification.
- Out of Scope:
  - Changes to tenant isolation for users who already have an assigned tenant.
  - Changes to workspace contextual resolution.

## Constraints & Delivery
- Delivery strategy: `ask-on-risk` (forecast ~60 lines < 400 lines).
- Verification trigger: Security/permissions change (requires thorough multi-suite verification).
- Conventional commits: No AI attribution.

## Actionable Tasks

- [x] `TASK-1`: Author OpenSpec lifecycle artifacts (`proposal.md`, `design.md`, delta spec `specs/contextual-authorization/spec.md`, `tasks.md`) in `openspec/changes/tenant-creation-without-membership/` and validate with OpenSpec CLI.
  - Route: Direct inline
  - Trigger evidence: OpenSpec documentation generation (<10k tokens)
  - Outcome: Validated via `openspec validate tenant-creation-without-membership` (passed with code 0).
- [x] `TASK-2`: Author RED automated test in `Monitor_Atlas/tests/test_contextual_permissions.py` simulating tenant creation by a user without tenant membership.
  - Route: Direct inline
  - Trigger evidence: Focused test addition
  - Outcome: Observed RED `AssertionError: 403 != 201`.
- [x] `TASK-3`: Implement permission exemption and direct user permission check in `Monitor_Atlas/roles/permissions.py`, turning test GREEN.
  - Route: Direct inline
  - Trigger evidence: Precision fix (<30 lines)
  - Outcome: Implemented tenant creation exemption and direct model permission check in `has_contextual_perm`; test passed GREEN.
- [x] `TASK-4`: Run full test suite across permissions, tenant context, adaptive auth, and multitenancy to ensure zero regressions; generate `verify-report.md`, archive change, and create work-unit commit.
  - Route: Direct inline
  - Trigger evidence: High-risk verification gate
  - Outcome: 14/14 passed in `test_contextual_permissions.py`, 14/14 passed in `test_tenant_context.py`, 40/40 passed in `test_adaptive_auth_sessions.py`, 11/11 passed in `test_support_multitenancy.py`, 11/11 passed in `test_device_measurement_consent.py`. Zero regressions.

## Verification Evidence
- Observed RED: `ContextualDRFPermissionTests.test_tenant_creation_allowed_for_user_without_tenant_membership` failed with `AssertionError: 403 != 201`.
- Observed GREEN:
  - `POSTGRES_HOST=127.0.0.1 venv/bin/pytest tests/test_contextual_permissions.py`: 14 passed in 2.45s
  - `POSTGRES_HOST=127.0.0.1 venv/bin/pytest tests/test_tenant_context.py`: 14 passed in 2.09s
  - `POSTGRES_HOST=127.0.0.1 venv/bin/pytest tests/test_adaptive_auth_sessions.py`: 40 passed in 34.30s
  - `POSTGRES_HOST=127.0.0.1 venv/bin/pytest tests/test_support_multitenancy.py`: 11 passed in 3.90s
  - `POSTGRES_HOST=127.0.0.1 venv/bin/pytest tests/test_device_measurement_consent.py`: 11 passed in 2.47s
- Django system check: `venv/bin/python manage.py check`: Passed with 0 issues.
- OpenSpec: Canonical specification `contextual-authorization` validated with code 0.
- Work-Unit Commit: `07393c9` (`fix(roles): allow tenant creation for users without tenant membership`).

## Next Step
- Feature complete. Ready for PR/merge review per repository policy.
