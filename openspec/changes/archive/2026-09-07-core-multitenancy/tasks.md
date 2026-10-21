# Tasks: Core Multitenancy

## Review Workload Forecast
- Estimated lines: ~250-350 lines
- Suggested split: single-pr
Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: size-exception
400-line budget risk: Low

---

## Phase 1: Foundation & Master Tenant Standardization

- [x] **1.1 Enforce Master Tenant Uniqueness at Database Level in `Monitor_Atlas/organizations/models.py`**
  - Update `Monitor_Atlas/organizations/models.py` to add `db_index=True` to `Tenant.is_global`.
  - Add a partial `UniqueConstraint` in `Tenant.Meta` restricting `is_global=True` to at most one record: `models.UniqueConstraint(fields=['is_global'], condition=models.Q(is_global=True), name='unique_global_tenant')`.
  - Generate and verify Django schema migration in `Monitor_Atlas/organizations/migrations/0002_tenant_unique_global.py`.

- [x] **1.2 Standardize Global Tenant Resolution Helper in `Monitor_Atlas/organizations/helpers.py`**
  - Update `Monitor_Atlas/organizations/helpers.py` to refine `get_global_tenant()`.
  - Ensure `get_global_tenant()` retrieves the designated master tenant via `Tenant.objects.filter(is_global=True).first()` with explicit error logging and clean exception handling if unconfigured.

- [x] **1.3 Eliminate Hardcoded Tenant String Checks in `Monitor_Atlas/organizations/views.py`**
  - Update `Monitor_Atlas/organizations/views.py` in `TenantViewSet.get_queryset` to replace string comparison `user.tenant.name == "Monitor"` with `bool(user.tenant and user.tenant.is_global)`.
  - Audit and refactor any auxiliary checks in `Monitor_Atlas/organizations/views.py` to use `is_global` or `get_global_tenant()` rather than tenant name literals.

---

## Phase 2: Core Implementation - Contextual Tenant Resolution Middleware

- [x] **2.1 Implement Tenant Context Resolution Middleware in `Monitor_Atlas/organizations/middleware.py`**
  - Create `Monitor_Atlas/organizations/middleware.py` implementing `TenantContextMiddleware`.
  - Parse `X-Tenant-ID` header from incoming HTTP request.
  - If `X-Tenant-ID` is present:
    - Look up `Tenant` by ID; return HTTP 404 if not found.
    - For authenticated users, verify tenant access: allow if `user.is_superuser`, or if `user.tenant and user.tenant.is_global`, or if user has an active membership in the target tenant via `WorkspaceMembership`.
    - Return HTTP 403 Forbidden if the user lacks authority to access the requested tenant.
    - Set `request.tenant = target_tenant` upon successful authorization.
  - If `X-Tenant-ID` is omitted:
    - Set `request.tenant = getattr(request.user, "tenant", None)` for authenticated requests; set `None` for unauthenticated requests.

- [x] **2.2 Register Middleware in Platform Settings `Monitor_Atlas/platform_backend/settings.py`**
  - Update `Monitor_Atlas/platform_backend/settings.py` to add `organizations.middleware.TenantContextMiddleware` to `MIDDLEWARE` immediately following authentication middleware (`JWTAuthMiddleware`).

- [x] **2.3 Contextualize Organization Viewsets to Active Tenant in `Monitor_Atlas/organizations/views.py`**
  - Update `TenantViewSet` in `Monitor_Atlas/organizations/views.py` to scope queries and permissions to `getattr(self.request, "tenant", None)`.
  - Update `WorkspaceViewSet` in `Monitor_Atlas/organizations/views.py` to scope `get_queryset` results to `request.tenant` for non-global users, preventing cross-tenant workspace visibility.
  - Refactor `WorkspaceViewSet.perform_create` in `Monitor_Atlas/organizations/views.py` to validate workspace creation against `request.tenant`.

---

## Phase 3: Wiring & Endpoints - Atomic User Tenant Transfer Service

- [x] **3.1 Implement Tenant Permission Revocation Helper in `Monitor_Atlas/roles/helpers.py`**
  - Update `Monitor_Atlas/roles/helpers.py` to add `revoke_user_tenant_permissions(user, source_tenant)`.
  - Purge all `WorkspaceMembership` records for `user` across all workspaces belonging to `source_tenant`.
  - Identify and disassociate all Django `Group`s linked to `source_tenant` roles from `user.groups`.
  - Remove all direct Guardian object-level permissions held by `user` for resources under `source_tenant`.

- [x] **3.2 Implement Atomic User Tenant Transfer Service in `Monitor_Atlas/users/services.py`**
  - Create `Monitor_Atlas/users/services.py` defining `UserTenantTransferService`.
  - Implement `UserTenantTransferService.transfer_user(user, destination_tenant, actor)` wrapped in `transaction.atomic`:
    - Validate pre-conditions: ensure `user` exists, destination tenant exists, and destination is distinct from source tenant (`user.tenant != destination_tenant`).
    - Execute `revoke_user_tenant_permissions(user, user.tenant)` to purge source tenant access.
    - Update `user.tenant = destination_tenant` and persist changes.
    - Retrieve destination default workspace via `get_or_create_default_workspace(destination_tenant)` and assign user with default "Sin rol" role.
    - Initialize base user permissions for new tenant via `assign_new_user_base_permissions(user)`.
    - Synchronize external ChirpStack account: if user has an associated `ApiUser`, update workspace reference and call `sync_api_user_update(api_user)`. Capture external errors in `api_user.sync_status = "ERROR"` and `api_user.sync_error` without rolling back the DB transaction.
    - Record immutable audit log entry in `django-auditlog` capturing target user, source tenant, destination tenant, actor, and timestamp.
    - Return transfer outcome data structure.

- [x] **3.3 Expose Transfer Action on User ViewSet in `Monitor_Atlas/users/views.py`**
  - Update `Monitor_Atlas/users/views.py` to add `@action(detail=True, methods=["post"], url_path="transfer_tenant", permission_classes=[IsAuthenticated, IsAnAdminUser])` to `UserViewSet`.
  - Validate request payload (`destination_tenant_id`) and handle validation errors with HTTP 400.
  - Invoke `UserTenantTransferService.transfer_user` passing target user, destination tenant, and `request.user`.
  - Return HTTP 200 with transfer summary or appropriate error responses.

---

## Phase 4: Verification & Automated Tests

- [x] **4.1 Unit Tests for Contextual Tenant Resolution in `Monitor_Atlas/tests/test_tenant_context.py`**
  - Create `Monitor_Atlas/tests/test_tenant_context.py` testing `TenantContextMiddleware`.
  - Test valid `X-Tenant-ID` resolves `request.tenant` for authorized user.
  - Test unauthorized `X-Tenant-ID` header yields HTTP 403 Forbidden.
  - Test non-existent `X-Tenant-ID` yields HTTP 404 Not Found.
  - Test fallback to `user.tenant` when `X-Tenant-ID` is omitted.
  - Test global administrator context switching across distinct tenants.

- [x] **4.2 Integration Tests for User Tenant Transfer in `Monitor_Atlas/tests/test_user_transfer.py`**
  - Create `Monitor_Atlas/tests/test_user_transfer.py` testing `UserTenantTransferService` and `POST /api/v1/users/{id}/transfer_tenant/`.
  - Test complete transfer lifecycle: verify source workspace memberships removed, role groups detached, direct Guardian permissions purged, default workspace assigned, and tenant assignment updated.
  - Test rejection of transfer when source and destination tenants are identical (HTTP 400).
  - Test rejection of transfer attempt by unauthorized non-admin user (HTTP 403).
  - Test audit log record creation in `LogEntry` verifying actor, target user, source, and destination tenant fields.

- [x] **4.3 Verify ChirpStack Error Handling and Transaction Rollback in `Monitor_Atlas/tests/test_user_transfer.py`**
  - In `Monitor_Atlas/tests/test_user_transfer.py`, verify ChirpStack sync failure handling: simulate external API timeout or HTTP 500, asserting `ApiUser.sync_status == "ERROR"` and `sync_error` recorded while database transaction commits successfully.
  - In `Monitor_Atlas/tests/test_user_transfer.py`, verify transactional rollback: simulate database error during transfer execution, asserting user tenant and permissions remain in their initial source state.
