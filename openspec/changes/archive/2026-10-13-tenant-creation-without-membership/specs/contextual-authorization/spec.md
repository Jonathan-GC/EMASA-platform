## MODIFIED Requirements

### Requirement: Contextual DRF Permission Class
The system MUST provide a contextual Django REST Framework permission class (`HasContextualPermission`) that enforces tenant and workspace authorization boundaries across all API viewsets. The permission class MUST resolve the active tenant and workspace context from the request (via request attributes, contextual headers such as `X-Tenant-ID` and `X-Workspace-ID`, query parameters, or route arguments) and map the HTTP method and view `scope` to the corresponding contextual permission codename. The permission class MUST deny access if the required context cannot be resolved for a scoped viewset, or if the user lacks the requisite contextual permission. When an authenticated user without an assigned tenant (`user.tenant is None`) creates a tenant (`scope == "tenant"` and action is `create` or `POST`), the permission class MUST NOT demand an active tenant context and MUST verify that the user possesses the `organizations.add_tenant` permission. The permission class MUST also support inter-service requests authenticated via configured service API keys.

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

#### Scenario: Tenant creation permitted for user without existing tenant membership
- GIVEN an authenticated user without any tenant membership (`user.tenant is None`)
- AND possessing direct `organizations.add_tenant` permission
- WHEN the user sends a `POST /api/v1/organizations/tenant/` request without an `X-Tenant-ID` header
- THEN `HasContextualPermission.has_permission` MUST permit the request without demanding an active tenant context.
