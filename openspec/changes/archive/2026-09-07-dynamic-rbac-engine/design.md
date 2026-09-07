# Design: Dynamic RBAC Engine

## Technical Approach
The dynamic RBAC engine eliminates cross-tenant and cross-workspace permission leakage caused by flat Django `user.groups`:
1. **Contextual Evaluation**: `has_contextual_perm()` checks permissions strictly against active `WorkspaceMembership.role.group` or Guardian object perms within `(user, tenant, workspace)`. Never falls back to global `user.groups` for scoped models. Superusers and global admins (`tenant.is_global=True`) bypass constraints.
2. **Contextual DRF Enforcement**: `HasContextualPermission` resolves `request.tenant` (from `TenantContextMiddleware`) and `workspace` (from `X-Workspace-ID` header, query params, or object), enforcing action mapping (`view_`, `add_`, `change_`, `delete_`) and object boundary ownership.
3. **Dynamic Permission Catalog**: `PermissionCatalogRegistry` centralizes assignable permissions across domain modules (`organizations`, `infrastructure`, `chirpstack`, `roles`, `users`, `support`). Exposes `GET /api/v1/roles/catalog/` and drives `get_assignable_permissions()`.
4. **Dynamic Frontend Rendering**: `RolePermissionsManager.vue` consumes `/api/v1/roles/catalog/` to dynamically render categories, labels, and icons without hardcoded maps.

## Architecture Decisions

### Decision: Contextual Permission Resolution vs Django Global Groups
| Option | Tradeoff | Decision |
| :--- | :--- | :--- |
| Django `user.has_perm()` | Leaks permissions across all assigned tenants/workspaces. | Rejected |
| Separate user accounts per tenant | Terrible UX, credential fragmentation, database bloat. | Rejected |
| Scoped `has_contextual_perm()` | Requires context resolution; guarantees zero-leakage isolation. | **Adopted** |

### Decision: Centralized Permission Catalog Registry
| Option | Tradeoff | Decision |
| :--- | :--- | :--- |
| Static presets (`GLOBAL_PERMISSIONS_PRESET` + UI maps) | Fragile, duplicative, rigid to extend. | Rejected |
| Raw `ContentType` DB introspection | Exposes internal models; lacks UI labels, icons, scopes. | Rejected |
| Declarative `PermissionCatalogRegistry` + API endpoint | Single source of truth; metadata-rich; dynamic UI rendering. | **Adopted** |

### Decision: DRF Permission Backward Compatibility
| Option | Tradeoff | Decision |
| :--- | :--- | :--- |
| Breaking rename of `HasPermission` | High regression risk; massive churn across viewsets. | Rejected |
| Refactor `HasPermission` as alias to `HasContextualPermission` | Seamless transition; immediate contextual enforcement. | **Adopted** |

## Data Flow
```
[Client Request] (Headers: X-Tenant-ID, X-Workspace-ID)
       ▼
[TenantContextMiddleware] ── Sets request.tenant
       ▼
[HasContextualPermission]
       │ 1. Resolves (tenant, workspace, scope, action)
       │ 2. Validates object ownership (obj.workspace == request.workspace)
       ▼
[has_contextual_perm()]
       │ Superuser or Global Admin? ──► [Allow]
       │ Query WorkspaceMembership(user=user, workspace=workspace)
       │ Verify perm in role.group or Guardian obj perms
       ▼
[Allow (200/201) or Deny (403 Forbidden)]
```

## File Changes
| File | Action | Description |
| :--- | :--- | :--- |
| `Monitor_Atlas/roles/catalog.py` | Create | Declarative `PermissionCatalogRegistry` for domain modules, actions, and scopes. |
| `Monitor_Atlas/roles/permissions.py` | Modify | Implement `has_contextual_perm()`, refactor `HasPermission` to `HasContextualPermission`. |
| `Monitor_Atlas/roles/helpers.py` | Modify | Refactor `get_assignable_permissions()` and bulk assignment to use catalog registry. |
| `Monitor_Atlas/roles/global_helpers.py` | Modify | Deprecate `GLOBAL_PERMISSIONS_PRESET` in favor of catalog registry. |
| `Monitor_Atlas/roles/views.py` | Modify | Add `GET /api/v1/roles/catalog/` endpoint to `RoleViewSet`. |
| `Monitor_Venus/src/components/forms/permissions/RolePermissionsManager.vue` | Modify | Fetch and render permission categories from catalog endpoint. |

## Interfaces / Contracts
### Contextual Evaluator
```python
def has_contextual_perm(
    user: User, perm: str, tenant: Tenant = None, workspace: Workspace = None, obj: Any = None
) -> bool:
    """Evaluates perm against user's active WorkspaceMembership.role.group or Guardian perms."""
```

### HTTP Endpoint: Permission Catalog
- `GET /api/v1/roles/catalog/` (Permissions: `IsAuthenticated`)
- Response (200 OK):
```json
{
  "categories": [
    {
      "key": "infrastructure",
      "label": "Infraestructura",
      "icon": "hardwareChip",
      "resources": [
        {"model": "device", "label": "Dispositivos", "scope": "workspace", "actions": ["view", "change", "delete"]}
      ]
    }
  ]
}
```

## Testing Strategy
- **Unit Tests**:
  - `has_contextual_perm()` allows access in matching workspace, blocks across workspaces and tenants.
  - Superuser and global admin bypass verification.
  - `PermissionCatalogRegistry` validates models against `ContentType` and auth permissions.
- **Integration Tests**:
  - `HasContextualPermission`: rejects missing context, enforces method actions, blocks cross-workspace/tenant object access (403/404).
  - Service API key bypass via `X-Service-API-Key`.
  - `GET /api/v1/roles/catalog/` filters platform actions for standard tenants.
  - `get_assignable_permissions()` bounds `can_assign` by caller's rights and excludes "Sin rol".

## Threat Matrix
| Threat | Severity | Mitigation |
| :--- | :--- | :--- |
| Cross-workspace permission leakage | Critical | `has_contextual_perm()` inspects only matching `WorkspaceMembership.role.group`. |
| Cross-tenant object mutation | Critical | `HasContextualPermission.has_object_permission()` validates tenant boundary match. |
| Privilege escalation via role assignment | High | `get_assignable_permissions()` bounds `can_assign` by caller's own perms. |
| Modification of protected roles | Medium | Assignment endpoints explicitly reject mutation of "Sin rol". |

## Migration / Rollout
1. **Catalog & Engine Deployment**: Deploy `catalog.py` and `has_contextual_perm()`.
2. **Permission Class Swap**: Replace `HasPermission` with `HasContextualPermission` (alias preserved).
3. **API Catalog Exposure**: Expose `RoleViewSet.catalog` action.
4. **Frontend Update**: Update `RolePermissionsManager.vue` to consume catalog endpoint.
5. **Rollback**: Revert `HasPermission` alias to legacy evaluator.

## Open Questions
- None. Context boundaries, registry models, and backward compatibility paths are fully resolved.
