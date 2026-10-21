# Tasks: Dynamic RBAC Engine

## Review Workload Forecast
- Estimated lines: ~300-380 lines
- 400-line budget risk: Low
- Chained PRs recommended: No
- Suggested split: single-pr
Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: size-exception
400-line budget risk: Low

---

## Phase 1: Permission Catalog Registry & Endpoints

- [x] **1.1 Create Permission Catalog Registry in `Monitor_Atlas/roles/catalog.py`**
  - Implement `PermissionCatalogRegistry` class as the centralized single source of truth for assignable platform permissions.
  - Declare registry data structures supporting domain categories (`organizations`, `infrastructure`, `chirpstack`, `roles`, `users`, `support`), display labels, icon identifiers, resource models, allowable actions (`view`, `change`, `delete`, `add`), and scope suitability (`workspace`, `tenant`, `global`).
  - Pre-register core platform models:
    - `organizations`: `tenant` (scope: tenant/global), `workspace` (scope: tenant/workspace)
    - `infrastructure`: `device`, `gateway`, `application`, `machine` (scope: workspace)
    - `chirpstack`: `deviceprofile`, `apiuser` (scope: workspace)
    - `roles`: `role`, `workspacemembership` (scope: workspace)
    - `users`: `user` (scope: tenant/workspace)
  - Implement `validate_registry()` method ensuring registered models correspond to valid Django `ContentType` and auth `Permission` codenames in the database.
  - Implement `get_catalog(tenant_type, scope)` filtering logic returning domain categories suitable for the caller's scope.

- [x] **1.2 Expose Catalog Action on RoleViewSet in `Monitor_Atlas/roles/views.py`**
  - Add `@action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])` named `catalog` to `RoleViewSet` in `Monitor_Atlas/roles/views.py`.
  - Inspect `request.user` and active tenant context: return standard tenant/workspace categories if `tenant.is_global=False`, and complete platform catalog including global system permissions if `user.is_superuser` or `tenant.is_global=True`.
  - Document the endpoint using `drf_spectacular.utils.extend_schema` specifying the response schema with categories, resources, actions, labels, and icons.
  - Reject unauthenticated requests with HTTP 401 Unauthorized.

- [x] **1.3 Refactor Assignable Permissions Calculation in `Monitor_Atlas/roles/helpers.py`**
  - Refactor `get_assignable_permissions(user, workspace, role)` in `Monitor_Atlas/roles/helpers.py` to query `PermissionCatalogRegistry` dynamically instead of relying on the static `object_models` dictionary.
  - Iterate through registered catalog resources for the target workspace, querying active instances for each model.
  - For each object, dynamically evaluate `assigned` status against `role.group` and `can_assign` status strictly bounded by the requesting administrator's permissions (`admin_group`).
  - Enforce protection for the default "Sin rol" role by immediately returning an empty assignable structure and blocking bulk permission updates.
  - Restrict assignable actions per tenant type: safe actions (`view`, `change`) for standard tenants vs full actions (`view`, `change`, `delete`) for global master tenants.
  - Deprecate static references to `GLOBAL_PERMISSIONS_PRESET` in `Monitor_Atlas/roles/global_helpers.py`.

---

## Phase 2: Contextual Permission Evaluator & Scoped DRF Class

- [x] **2.1 Implement Contextual Permission Evaluator in `Monitor_Atlas/roles/permissions.py`**
  - Implement `has_contextual_perm(user, perm, tenant=None, workspace=None, obj=None)` in `Monitor_Atlas/roles/permissions.py`.
  - Allow bypass for superusers (`user.is_superuser=True`) returning `True`.
  - Allow bypass for global administrators (`tenant and tenant.is_global=True` with `global_admin` role) while generating audit log records.
  - For standard requests, resolve the user's active `WorkspaceMembership` matching `(user=user, workspace=workspace)`.
  - Check whether `perm` is granted by `membership.role.group` or assigned as a direct Guardian object permission on `obj`.
  - Strictly prevent fallback to global Django `user.groups` or permissions from other workspaces, ensuring zero cross-workspace and cross-tenant leakage.
  - Return `False` for unauthenticated requests or users without active role assignments in the specified workspace.

- [x] **2.2 Refactor HasPermission into HasContextualPermission in `Monitor_Atlas/roles/permissions.py`**
  - Implement `HasContextualPermission(BasePermission)` in `Monitor_Atlas/roles/permissions.py`.
  - In `has_permission(request, view)`:
    - Resolve active `tenant` from `request.tenant` (injected by `TenantContextMiddleware`).
    - Resolve active `workspace` from `X-Workspace-ID` header, query parameter `workspace`, or view kwargs; reject with HTTP 400/403 if context is unresolvable on scoped viewsets.
    - Map HTTP method to action codename (`GET`/`HEAD`/`OPTIONS` -> `view_{scope}`, `POST` -> `add_{scope}`, `PUT`/`PATCH` -> `change_{scope}`, `DELETE` -> `delete_{scope}`).
    - Map custom action decorators (`set_activation`, `create_measurement`, etc.) to respective permission codenames.
    - Evaluate action permission via `has_contextual_perm(request.user, perm_name, tenant=tenant, workspace=workspace)`.
  - In `has_object_permission(request, view, obj)`:
    - Verify object ownership boundary: validate `obj.workspace == request.workspace` (or `obj.tenant == request.tenant`); return HTTP 403/404 on boundary mismatch.
    - Traverse nested object hierarchies if applicable to enforce parent workspace ownership.
    - Evaluate object-level permission via `has_contextual_perm(request.user, perm_name, tenant=tenant, workspace=workspace, obj=obj)`.
  - Support internal service authentication via `X-Service-API-Key` or `X-API-Key` matching `settings.SERVICE_API_KEY`.
  - Retain `HasPermission = HasContextualPermission` alias to maintain backward compatibility across existing viewsets.

- [x] **2.3 Update Scoped Viewsets in `Monitor_Atlas/roles/views.py` and `Monitor_Atlas/organizations/views.py`**
  - Update `RoleViewSet` and `WorkspaceMembershipViewSet` in `Monitor_Atlas/roles/views.py` to use `HasContextualPermission` and verify contextual workspace filtering in `get_queryset`.
  - Update `WorkspaceViewSet`, `TenantViewSet`, and `SubscriptionViewSet` in `Monitor_Atlas/organizations/views.py` to adopt `HasContextualPermission`.
  - Validate that object retrieval, mutation, and deletion across these viewsets enforce tenant and workspace ownership boundaries.

---

## Phase 3: Frontend Dynamic Catalog Integration

- [x] **3.1 Update `Monitor_Venus/src/components/forms/permissions/RolePermissionsManager.vue` to Fetch Catalog Endpoint from `Monitor_Atlas/roles/views.py`**
  - Refactor `RolePermissionsManager.vue` to fetch `/api/v1/roles/catalog/` dynamically on mount via backend endpoint in `Monitor_Atlas/roles/views.py`.
  - Remove hardcoded `categoryLabels` and `categoryIcons` dictionaries, replacing them with dynamic metadata (`key`, `label`, `icon`, `resources`) provided by the catalog response.
  - Dynamically render categories, item cards, and permission checkboxes matching the catalog structure.
  - Preserve toggle logic and payload formatting for bulk permission updates to `RoleViewSet.bulk_assign_permissions`.
  - Gracefully handle loading spinners, empty permission categories, and error notifications.

- [x] **3.2 Update `Monitor_Venus/src/components/forms/update/roles/formUpdateRoles.vue` to Dynamically Bind Permissions Defined in `Monitor_Atlas/roles/catalog.py`**
  - Refactor `fetchPermissions()` in `formUpdateRoles.vue` to consume dynamic catalog definitions from `Monitor_Atlas/roles/catalog.py` and `Monitor_Atlas/roles/views.py`.
  - Bind available permissions dynamically to form state instead of relying on static placeholders.
  - Ensure updated role permissions payloads adhere to catalog action codenames and are validated prior to form submission.

---

## Phase 4: Automated Testing & Verification

- [x] **4.1 Automated Tests for Permission Catalog Registry & Endpoints in `Monitor_Atlas/tests/test_permission_catalog.py`**
  - Create `Monitor_Atlas/tests/test_permission_catalog.py` testing the catalog registry and API endpoint.
  - Test registration, retrieval, and schema structure of categories in `PermissionCatalogRegistry`.
  - Test `validate_registry()` ensures all registered models match valid `ContentType` and Django auth permissions.
  - Test `GET /api/v1/roles/catalog/` returns HTTP 200 with structured JSON for authenticated users and HTTP 401 for anonymous users.
  - Test catalog response filtering: verify standard tenant users receive only tenant/workspace scoped permissions, while global admins receive full platform catalog.
  - Test `get_assignable_permissions()` dynamically includes objects for registered models and accurately computes `assigned` and `can_assign` flags based on caller rights.
  - Test "Sin rol" returns empty assignable permissions and rejects bulk permission mutation.

- [x] **4.2 Automated Tests for Contextual Permission Isolation in `Monitor_Atlas/tests/test_contextual_permissions.py`**
  - Create `Monitor_Atlas/tests/test_contextual_permissions.py` testing `has_contextual_perm` and `HasContextualPermission`.
  - Test positive permission evaluation: user with role in active workspace is granted access.
  - Test cross-workspace isolation: user with permission in Workspace A is denied access in Workspace B within the same tenant.
  - Test cross-tenant isolation: user with permissions in Tenant 1 is denied access in Tenant 2 (zero global group leakage).
  - Test superuser and global administrator cross-tenant management bypass.
  - Test viewset enforcement with `HasContextualPermission`: verify HTTP 403 on missing permissions and HTTP 400/403 when active workspace/tenant context cannot be resolved.
  - Test object-level ownership check: attempting to access an object belonging to another workspace or tenant returns HTTP 403 or HTTP 404.
  - Test inter-service authentication bypass using `X-Service-API-Key` header.
