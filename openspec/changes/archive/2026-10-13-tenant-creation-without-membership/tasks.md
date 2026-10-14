## 1. Automated Test Suite (RED)

- [ ] 1.1 Add test verifying a user with `user.tenant is None` and `organizations.add_tenant` can create a tenant via `POST /api/v1/organizations/tenant/` without an `X-Tenant-ID` header

## 2. Implementation (GREEN)

- [ ] 2.1 Update `HasContextualPermission.has_permission` in `Monitor_Atlas/roles/permissions.py` to exempt tenant creation when `user.tenant is None`
- [ ] 2.2 Update `has_contextual_perm` in `Monitor_Atlas/roles/permissions.py` to evaluate direct user model permissions when `workspace is None and tenant is None`

## 3. Verification & Governance

- [ ] 3.1 Run tests in `test_contextual_permissions.py` and full regression suites to confirm zero regressions
- [ ] 3.2 Validate OpenSpec state, generate `verify-report.md`, and archive change
