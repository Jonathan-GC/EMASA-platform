# Tenant Isolation Specification

## Purpose
Defines the rules, protocols, and mechanisms for identifying master/global tenants, resolving tenant context per request, and enforcing strict data isolation boundaries across tenants without hardcoded identifiers.

## ADDED Requirements

### Requirement: Formal Master Tenant Identification
The system MUST identify master (global platform) tenants exclusively through the boolean attribute `Tenant.is_global` or dedicated system accessor functions such as `get_global_tenant()`. Application code, views, permission handlers, and queries MUST NOT compare tenant names against hardcoded string literals (such as `"Monitor"`). At most one tenant SHALL have `is_global=True` at any given time, enforced by validation and database constraints. Global administrative roles and presets MUST only apply to users affiliated with an `is_global=True` tenant or superusers.

#### Scenario: Retrieval of global master tenant via is_global attribute
- GIVEN a database containing multiple tenants where exactly one tenant has `is_global=True` and all other tenants have `is_global=False`
- WHEN the application queries for the master tenant using `Tenant.objects.filter(is_global=True).first()` or `get_global_tenant()`
- THEN the system MUST return the designated global tenant instance
- AND the lookup MUST NOT depend on the tenant's `name` attribute.

#### Scenario: Prevention of multiple global tenants
- GIVEN an existing tenant record with `is_global=True`
- WHEN an administrator or service attempts to create or update another tenant with `is_global=True`
- THEN the system MUST reject the creation or update with a validation error
- AND the existing global tenant designation MUST remain unaltered.

#### Scenario: Removal of hardcoded tenant name string comparisons
- GIVEN any endpoint or service evaluating platform-wide administrative privileges (such as `TenantViewSet.get_queryset` or `get_assignable_permissions`)
- WHEN an authenticated user executes a request
- THEN the authorization check MUST evaluate `user.tenant.is_global` or global group memberships (`global_admin`, `global_manager`, `global_technician`)
- AND the authorization check MUST NOT evaluate `user.tenant.name == "Monitor"` or any hardcoded name literal.

### Requirement: Active Tenant Resolution and Contextual Scoping
The system MUST resolve the active tenant context for every authenticated request. Clients MAY supply an `X-Tenant-ID` HTTP header to explicitly scope requests to a specific tenant. If the `X-Tenant-ID` header is supplied, the system MUST verify that the authenticated user has authorization to access the requested tenant before setting the active tenant context. If no header is provided, the system MUST fall back to the authenticated user's primary assigned tenant.

#### Scenario: Explicit tenant context resolution via valid X-Tenant-ID header
- GIVEN an authenticated user possessing valid membership or authorization in tenant "tenant-beta"
- WHEN the user sends an HTTP request containing the header `X-Tenant-ID: tenant-beta`
- THEN the system MUST resolve the active tenant context to "tenant-beta"
- AND all downstream queryset filtering in the request lifecycle MUST be scoped to "tenant-beta".

#### Scenario: Rejection of unauthorized X-Tenant-ID header
- GIVEN an authenticated user who is NOT a member of tenant "tenant-gamma" and does NOT possess global administrative authority
- WHEN the user sends an HTTP request containing the header `X-Tenant-ID: tenant-gamma`
- THEN the system MUST reject the request with an HTTP 403 Forbidden response
- AND no data from "tenant-gamma" SHALL be returned.

#### Scenario: Rejection of non-existent X-Tenant-ID header
- GIVEN an authenticated user
- WHEN the user sends an HTTP request containing `X-Tenant-ID: invalid-tenant-id` that does not exist in the database
- THEN the system MUST reject the request with an HTTP 404 Not Found response.

#### Scenario: Fallback to primary tenant when X-Tenant-ID is omitted
- GIVEN an authenticated user whose primary assigned tenant is "tenant-alpha"
- WHEN the user sends an HTTP request without an `X-Tenant-ID` header
- THEN the system MUST resolve the active tenant context to "tenant-alpha"
- AND all queries for tenant-scoped resources MUST default to "tenant-alpha".

#### Scenario: Global administrator tenant switching via X-Tenant-ID
- GIVEN an authenticated user associated with an `is_global=True` tenant possessing global administrator role (`is_superuser=True` or `global_admin` group)
- WHEN the user sends a request with `X-Tenant-ID: tenant-customer-a`
- THEN the system MUST accept the header and set the active tenant context to "tenant-customer-a"
- AND the response MUST include resources scoped to "tenant-customer-a".

### Requirement: Isolation Boundary Enforcement
The system MUST strictly enforce tenant isolation boundaries across all queries, mutations, and object-level permissions. Tenant users MUST NOT be able to view, edit, or delete resources (such as workspaces, devices, gateways, roles, or users) belonging to any tenant other than their active tenant context. Cross-tenant access SHALL only be permitted for users with verified global administrative privileges originating from a global tenant (`is_global=True`).

#### Scenario: Tenant queryset filtering strictly isolated to active tenant
- GIVEN two isolated tenants, "Tenant A" and "Tenant B", each containing distinct workspaces and devices
- AND an authenticated user belonging exclusively to "Tenant A" with active tenant context "Tenant A"
- WHEN the user queries the list endpoint for workspaces or devices
- THEN the returned queryset MUST contain only resources belonging to "Tenant A"
- AND resources belonging to "Tenant B" MUST NOT appear in the results.

#### Scenario: Direct object retrieval across tenant boundaries rejected
- GIVEN a workspace "WS-B-1" belonging to "Tenant B"
- AND an authenticated user whose active tenant context is "Tenant A"
- WHEN the user attempts to retrieve, update, or delete "WS-B-1" via `GET /api/v1/organizations/workspaces/WS-B-1/`
- THEN the system MUST deny the request with an HTTP 404 Not Found or HTTP 403 Forbidden response
- AND no modification or data disclosure of "WS-B-1" SHALL occur.

#### Scenario: Global administrator cross-tenant management
- GIVEN a global administrative user affiliated with the master tenant (`is_global=True`)
- WHEN the global administrator requests tenant or workspace collections across the platform
- THEN the system MUST allow access based on the global administrative permission preset (`global_admin`)
- AND the system MUST maintain audit logging for all cross-tenant actions executed by the administrator.

#### Scenario: Object-level permission scoping avoids leakage
- GIVEN a user with object-level permissions granted via Django Guardian in "Tenant A"
- WHEN the user's active tenant context is evaluated
- THEN Guardian queries MUST NOT evaluate permissions against objects belonging to "Tenant B"
- AND the system MUST ensure role-based group permissions are bounded by tenant hierarchy.
