# dynamic-permission-catalog Specification

## Purpose
Defines the structure, registry mechanisms, API endpoint, and dynamic calculation of assignable permissions across the platform. This replaces hardcoded permission presets (`GLOBAL_PERMISSIONS_PRESET`) and frontend UI dictionaries with a dynamic, metadata-rich permission catalog organized by domain categories, resources, allowable actions, and scope suitability.
## Requirements
### Requirement: Centralized Permission Catalog Registry
The system MUST provide a centralized permission catalog registry as the single source of truth for all assignable permissions across the platform. The registry MUST categorize permissions into domain modules, including `organizations`, `infrastructure`, `chirpstack`, `roles`, and `support`. Each registered entry MUST declare its category key, human-readable display label, UI icon identifier, registered resource models, allowable actions (`view`, `change`, `delete`, `add`), and scope suitability (`workspace`, `tenant`, or `global`). The registry MUST validate that declared permissions map to valid Django `ContentType` and auth permission codenames.

#### Scenario: Registration and discovery of permission categories
- GIVEN the application initializes its permission registry
- WHEN the registry registers categories for `organizations`, `infrastructure`, `chirpstack`, `roles`, and `support`
- THEN all registered categories MUST be discoverable through the central catalog registry API
- AND each category MUST provide its display label, icon, and managed resource models.

#### Scenario: Scope suitability declaration and filtering
- GIVEN a permission entry in the catalog defining actions on workspace resources
- WHEN the entry declares `scope_suitability="workspace"`
- THEN the catalog registry MUST flag this permission as assignable within workspace-level roles
- AND permissions flagged with `scope_suitability="global"` MUST NOT be assignable to standard tenant workspace roles.

#### Scenario: ContentType and permission codename validation
- GIVEN a new resource model registered in the catalog with allowed actions `["view", "change", "delete"]`
- WHEN the registry validates the entry against the database ContentTypes
- THEN the registry MUST ensure corresponding Django `Permission` records exist
- AND any missing permission codename MUST trigger a configuration warning or validation error.

#### Scenario: Extensibility for new domain modules
- GIVEN a new platform application module requiring role-based access control
- WHEN the module registers its models, labels, and actions with the catalog registry
- THEN the catalog registry MUST immediately include the new module in catalog queries
- AND existing core RBAC code MUST NOT require modification.

### Requirement: Permission Catalog Endpoint
The system MUST expose a dedicated HTTP endpoint `GET /api/v1/roles/catalog/` that returns the structured permission catalog dynamically. The endpoint MUST return domain categories, resource models, supported actions, human-readable labels, and icons. The endpoint MUST filter returned categories and permissions according to the caller's authorization context: standard tenant users MUST only receive permissions suitable for their tenant or workspace scope, while global administrators affiliated with a master tenant (`is_global=True`) MUST receive the complete catalog. Unauthenticated requests MUST be rejected with HTTP 401 Unauthorized.

#### Scenario: Successful retrieval of permission catalog by workspace administrator
- GIVEN an authenticated user possessing workspace administrative privileges within a standard tenant
- WHEN the user sends a `GET /api/v1/roles/catalog/` request
- THEN the system MUST return an HTTP 200 OK response containing the permission catalog
- AND each category in the response MUST include `key`, `label`, `icon`, and list of `resources` with allowable actions
- AND platform-level global administrative permissions MUST be excluded from the response.

#### Scenario: Full catalog retrieval by global administrator
- GIVEN an authenticated user affiliated with a global master tenant (`is_global=True`) possessing the `global_admin` role
- WHEN the user sends a `GET /api/v1/roles/catalog/` request
- THEN the system MUST return the complete catalog including global system permissions, cross-tenant management scopes, and administrative actions.

#### Scenario: Rejection of unauthenticated catalog request
- GIVEN an unauthenticated client request
- WHEN the client sends a `GET /api/v1/roles/catalog/` request
- THEN the system MUST reject the request with an HTTP 401 Unauthorized response
- AND no catalog metadata SHALL be returned.

#### Scenario: Frontend schema compatibility
- GIVEN frontend role management components (`formUpdateRoles.vue`, `RolePermissionsManager.vue`)
- WHEN the components query `GET /api/v1/roles/catalog/`
- THEN the response payload MUST provide structured labels, icons, and item categories enabling dynamic rendering without frontend-hardcoded permission dictionaries.

### Requirement: Dynamic Assignable Permissions Generation
The system MUST dynamically generate assignable permissions for roles by querying the centralized permission catalog registry rather than inspecting hardcoded model lists. The calculation logic in `get_assignable_permissions` MUST inspect the target role's workspace, query existing objects for each catalog resource within that workspace, and determine for every allowed action whether the permission is currently assigned (`assigned`) and whether the requesting user has the authority to grant or revoke it (`can_assign`). The system MUST enforce that `can_assign` is strictly bounded by the requesting user's own permissions. The system MUST reject assignable permission generation for protected default roles such as "Sin rol".

#### Scenario: Dynamic calculation of assignable permissions for a workspace role
- GIVEN an authenticated workspace administrator requesting assignable permissions for a custom role in "Workspace Alpha"
- WHEN `RoleViewSet.get_assignable_permissions` or `get_assignable_permissions()` is invoked
- THEN the system MUST iterate over resource models registered in the catalog for the workspace
- AND for each object in the workspace, the system MUST compute `assigned` status for the target role's group
- AND the system MUST compute `can_assign` status based on the requesting administrator's permissions.

#### Scenario: Administrative authority bounding of assignable permissions
- GIVEN an authenticated user managing a role in "Workspace Alpha" who has "view_device" but lacks "delete_device"
- WHEN the system calculates assignable permissions for a target role
- THEN `can_assign` for "delete_device" MUST be evaluated as `False`
- AND the user MUST NOT be permitted to grant "delete_device" to any role.

#### Scenario: Exclusion of protected default role "Sin rol"
- GIVEN a role named "Sin rol" representing the default unprivileged role
- WHEN an administrator or client queries assignable permissions for "Sin rol"
- THEN the system MUST return an empty assignable permissions structure
- AND bulk permission assignment on "Sin rol" MUST be rejected with an appropriate error.

#### Scenario: Scope-aware action restrictions for tenant types
- GIVEN a workspace belonging to a standard tenant (`is_global=False`)
- WHEN assignable permissions are generated for a role in that workspace
- THEN the system MUST restrict allowable actions to safe tenant actions defined in the catalog (`view`, `change`)
- AND destructive platform actions designated exclusively for global master tenants MUST NOT be marked assignable.

#### Scenario: Dynamic adaptation to catalog expansion
- GIVEN a new model registered in the centralized permission catalog under the "infrastructure" category
- WHEN assignable permissions are calculated for a workspace containing instances of the new model
- THEN the new model and its objects MUST automatically appear in the `assignable_permissions` response
- AND no manual updates to `get_assignable_permissions` codebase SHALL be required.

