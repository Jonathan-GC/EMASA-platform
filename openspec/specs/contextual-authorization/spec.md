# contextual-authorization Specification

## Purpose
Defines the rules, evaluation algorithms, and authorization boundaries for context-scoped permission evaluation across `(user, tenant, workspace)` tuples. This eliminates global permission leakage caused by flat Django `user.groups` memberships, provides a contextual Django REST Framework permission class, and enforces strict object-level contextual ownership across tenant and workspace boundaries.
## Requirements
### Requirement: Contextual Scope Permission Evaluation
The system MUST evaluate user permissions strictly within the context of the active tenant and workspace `(user, tenant, workspace)`. The permission evaluation engine MUST NOT rely on flat Django `user.groups` or global `user.has_perm()` calls that aggregate permissions across unrelated workspaces and tenants. When evaluating whether a user has permission to perform an action on a resource within a workspace, the system MUST verify that the user holds an active role or membership within that specific workspace granting the requisite permission. Permissions granted to a user within one workspace SHALL NOT leak or confer privileges within any other workspace or tenant.

#### Scenario: Permission evaluation within assigned workspace context
- GIVEN an authenticated user who is assigned a role granting "add_device" within "Workspace Alpha" of "Tenant One"
- WHEN the user attempts to create a device with the active request context set to "Workspace Alpha"
- THEN the contextual evaluation engine MUST evaluate the user's role permissions within "Workspace Alpha"
- AND the system MUST grant authorization for the action.

#### Scenario: Denial of permission across workspaces within the same tenant
- GIVEN an authenticated user who has a role granting "delete_device" in "Workspace Alpha"
- AND the same user has a role granting only "view_device" in "Workspace Beta" within the same tenant
- WHEN the user attempts to delete a device with the active context set to "Workspace Beta"
- THEN the contextual evaluation engine MUST evaluate permissions strictly within "Workspace Beta"
- AND the system MUST reject the deletion request with an authorization error
- AND permissions from "Workspace Alpha" MUST NOT be evaluated or conferred.

#### Scenario: Strict tenant boundary isolation preventing cross-tenant permission leakage
- GIVEN a user with administrative role permissions in "Tenant One"
- AND the user has no membership or role in "Tenant Two"
- WHEN the user attempts to perform any action with active context set to "Tenant Two"
- THEN the contextual evaluation engine MUST detect the absence of authorized membership in "Tenant Two"
- AND the system MUST reject the request with an authorization failure
- AND the user's group memberships in "Tenant One" MUST NOT confer any permissions in "Tenant Two".

#### Scenario: Multi-role membership isolation within a single user account
- GIVEN a user belonging to multiple workspaces with differing roles ("Manager" in Workspace 1, "Viewer" in Workspace 2)
- WHEN evaluating a write action in Workspace 2
- THEN the contextual evaluator MUST inspect only the role bound to Workspace 2
- AND permissions granted by the "Manager" role in Workspace 1 MUST NOT leak into Workspace 2.

#### Scenario: Superuser contextual evaluation bypass
- GIVEN an authenticated user with `is_superuser=True`
- WHEN any contextual permission check is performed across any tenant or workspace
- THEN the contextual evaluation engine MUST bypass workspace-specific role constraints and return True.

#### Scenario: Global administrator cross-tenant management evaluation
- GIVEN an authenticated user affiliated with a global master tenant (`is_global=True`) possessing the `global_admin` role
- WHEN the user performs an administrative operation within any tenant or workspace context
- THEN the contextual permission evaluation MUST validate the user's global administrator status
- AND the system MUST allow the operation while recording audit logs for the cross-tenant action.

### Requirement: Contextual DRF Permission Class
The system MUST provide a contextual Django REST Framework permission class (`HasContextualPermission`) that enforces tenant and workspace authorization boundaries across all API viewsets. The permission class MUST resolve the active tenant and workspace context from the request (via request attributes, contextual headers such as `X-Tenant-ID` and `X-Workspace-ID`, query parameters, or route arguments) and map the HTTP method and view `scope` to the corresponding contextual permission codename. The permission class MUST deny access if the required context cannot be resolved for a scoped viewset, or if the user lacks the requisite contextual permission. The permission class MUST also support inter-service requests authenticated via configured service API keys.

#### Scenario: Authorized viewset request with valid contextual permission
- GIVEN an authenticated user with "view_device" permission in active workspace "Workspace Alpha"
- WHEN the user sends a `GET /api/v1/infrastructure/devices/` request scoped to "Workspace Alpha"
- THEN `HasContextualPermission.has_permission` MUST verify the user's permission for scope "device" and action "view" in "Workspace Alpha"
- AND the request MUST be permitted to proceed to the viewset handler.

#### Scenario: Viewset request denied due to lack of contextual permission
- GIVEN an authenticated user with only "view_device" permission in active workspace "Workspace Alpha"
- WHEN the user sends a `POST /api/v1/infrastructure/devices/` request to create a new device in "Workspace Alpha"
- THEN `HasContextualPermission.has_permission` MUST determine that "add_device" is required in "Workspace Alpha"
- AND the system MUST reject the request with an HTTP 403 Forbidden response.

#### Scenario: Missing or unresolvable active context on scoped viewset
- GIVEN a request to a scoped viewset where neither workspace nor tenant context can be resolved from the request
- WHEN `HasContextualPermission.has_permission` evaluates the request
- THEN the permission class MUST reject the request with an HTTP 400 Bad Request or HTTP 403 Forbidden response
- AND un-scoped global permission evaluation MUST NOT be performed.

#### Scenario: Custom viewset action permission evaluation
- GIVEN a custom action on a viewset declared with a custom action identifier (such as `activate` or `set_activation`)
- WHEN an authenticated user invokes the custom action on the viewset
- THEN `HasContextualPermission` MUST map the custom action to the designated permission codename
- AND the permission check MUST evaluate whether the user holds that permission within the active workspace context.

#### Scenario: Inter-service request authentication via service API key
- GIVEN an incoming request bearing a valid service API key header matching `settings.SERVICE_API_KEY`
- WHEN `HasContextualPermission.has_permission` evaluates the request
- THEN the system MUST authenticate the request as an internal trusted service
- AND user-level contextual role checks SHALL be bypassed.

### Requirement: Object-Level Contextual Ownership
The system MUST verify that any target object requested for retrieval, modification, or deletion strictly belongs to the request's active tenant and workspace context. In `has_object_permission`, the system MUST reject any operation if the target object's tenant or workspace does not match the active request context, regardless of whether the user possesses permissions on an object with the same ID in another context. Object-level permission evaluation MUST inspect direct ownership or parent relationships (`object.workspace` and `object.tenant`) and verify that the user holds the requisite object permission within that specific contextual boundary.

#### Scenario: Permitted object modification within matching context
- GIVEN an object "Device 101" belonging to "Workspace Alpha" in "Tenant One"
- AND an authenticated user possessing contextual "change_device" permission in "Workspace Alpha"
- WHEN the user sends a `PUT /api/v1/infrastructure/devices/101/` request with active context "Workspace Alpha"
- THEN the system MUST verify that "Device 101" belongs to "Workspace Alpha"
- AND the system MUST verify that the user has "change_device" on the object within "Workspace Alpha"
- AND the modification request MUST be permitted.

#### Scenario: Rejection of object access across workspace boundaries
- GIVEN an object "Device 202" belonging to "Workspace Beta"
- AND an authenticated user operating with active context set to "Workspace Alpha" within the same tenant
- WHEN the user attempts to retrieve or update "Device 202" via `GET /api/v1/infrastructure/devices/202/`
- THEN the system MUST detect that the object's workspace does not match the active request workspace
- AND the system MUST reject the request with an HTTP 404 Not Found or HTTP 403 Forbidden response
- AND no data from "Device 202" SHALL be disclosed or modified.

#### Scenario: Rejection of object access across tenant boundaries
- GIVEN an object "Gateway 303" belonging to "Tenant Two"
- AND an authenticated user operating with active context set to "Tenant One"
- WHEN the user attempts to access or mutate "Gateway 303"
- THEN the system MUST determine that "Gateway 303" belongs to "Tenant Two"
- AND the system MUST reject the request with an HTTP 404 Not Found or HTTP 403 Forbidden response.

#### Scenario: Hierarchical ownership verification for nested resources
- GIVEN a nested resource that references a parent entity (such as a device measurement linked to a device)
- WHEN an object-level permission check is executed
- THEN the system MUST traverse the hierarchy to verify parent workspace and tenant ownership
- AND any mismatch between the parent resource's context and the active request context MUST result in access denial.

#### Scenario: Superuser and global administrator object-level access
- GIVEN an authenticated superuser or global administrator from a global master tenant (`is_global=True`)
- WHEN the user accesses an object in any workspace or tenant
- THEN the system MUST verify platform-level administrative authority and allow access
- AND the system MUST record audit logs for cross-boundary administrative operations.

