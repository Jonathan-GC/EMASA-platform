# Proposal: Dynamic RBAC Engine

## Intent
Eliminate global permission leakage caused by flat Django `user.groups` assignment across workspaces/tenants, and replace hardcoded permission dictionaries in backend (`GLOBAL_PERMISSIONS_PRESET`) and frontend with a dynamic, scoped RBAC engine and permission catalog.

## Scope
### In Scope
- **Contextual Permission Evaluation**: Scoped permission checker evaluating permissions strictly within `(user, tenant, workspace)` context, preventing permissions granted in one workspace from leaking globally to other tenants.
- **Dynamic Permission Catalog**: Centralize permission definitions into a discoverable catalog endpoint (`/api/v1/roles/catalog/`) exposing categories, resources, and allowable actions without hardcoded UI lists.
- **Dynamic Role Permissions Management**: Refactor assignable permissions API and frontend integration (`formUpdateRoles.vue`, `RolePermissionsManager.vue`) to dynamically consume the permission catalog.
- **Migration & Backward Compatibility**: Safe migration of existing `Role` and `WorkspaceMembership` permission assignments to the contextual model without downtime.

### Out of Scope
- Support ticket permission scoping and technician cross-tenant dispatch (reserved for SDD 3).

## Capabilities
### New Capabilities
- contextual-authorization: Context-scoped permission checks `(user, tenant, workspace)` preventing cross-workspace/cross-tenant privilege escalation.
- dynamic-permission-catalog: Discoverable metadata catalog of assignable permissions by scope.

### Modified Capabilities
- None

## Approach
- Introduce context-aware evaluation in `Monitor_Atlas/roles/permissions.py` and `helpers.py` taking `(user, tenant, workspace)` instead of relying on flat `user.groups` or global permissions.
- Implement permission catalog service and endpoint in `Monitor_Atlas/roles/views.py` exposing structured permissions by category, resource, and scope.
- Replace `GLOBAL_PERMISSIONS_PRESET` and static dictionaries with dynamic catalog queries.
- Update frontend role forms to fetch permission schema dynamically from `/api/v1/roles/catalog/` instead of hardcoded lists.
- Provide data migration script to re-index and validate existing role assignments against tenant/workspace boundaries.

## Affected Areas
| Component | Files |
|---|---|
| Backend Models & Helpers | `Monitor_Atlas/roles/models.py`<br>`Monitor_Atlas/roles/helpers.py`<br>`Monitor_Atlas/roles/global_helpers.py` |
| Backend API & Permissions | `Monitor_Atlas/roles/permissions.py`<br>`Monitor_Atlas/roles/views.py` |
| Frontend Components | `Monitor_Venus/src/components/forms/update/roles/formUpdateRoles.vue`<br>`Monitor_Venus/src/components/forms/permissions/RolePermissionsManager.vue` |

## Risks
- **Permission Denial During Transition**: In-flight requests during migration might miss contextual assignments. *Mitigation*: Fallback grace resolution with deprecation telemetry.
- **Frontend State Desynchronization**: UI rendering issues if catalog schema mismatch occurs. *Mitigation*: Versioned catalog response format and schema fallback validation.

## Rollback Plan
- Revert Git changes across backend and frontend repositories.
- Roll back database migrations via `python manage.py migrate roles <previous_migration>`.
- Restore fallback to previous group-based assignment if contextual checks encounter unforeseen edge cases.

## Dependencies
- Django ORM & migrations.
- Django REST Framework authorization stack.
- Vue 3 / Pinia stores in `Monitor_Venus`.

## Success Criteria
- Zero permission leakage between tenants or distinct workspaces in unit/integration tests.
- Backend `/api/v1/roles/catalog/` returns complete dynamic permission hierarchy.
- Frontend role management components render dynamically without hardcoded permission lists.
- Existing roles and workspace memberships migrate cleanly with zero permission loss.
