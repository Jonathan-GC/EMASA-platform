# support-multitenancy Specification

## Purpose
Defines the tenant isolation and contextual access control rules for the support subsystem in `Monitor_Atlas`. It establishes formal database-level associations between support resources (`Ticket`, `SupportMembership`) and tenants (`Tenant`, and optional `Workspace`), enforces strict multi-tenant authorization boundaries on all support endpoints (`TicketViewSet`, `CommentViewSet`, `AttachmentViewSet`, `CommentAttachmentViewSet`, `SupportMembershipViewSet`) using `HasContextualPermission`, and guarantees that comments and attachments inherit their parent ticket's tenant isolation to prevent unauthorized cross-tenant data leakage.
## Requirements
### Requirement: Support Resource Tenant Association
The system MUST link `Ticket` to `Tenant` via a non-nullable foreign key (`Ticket.tenant`). The system MUST link `Ticket` to an optional `Workspace` via a nullable foreign key (`Ticket.workspace`), which if provided MUST belong to the associated `tenant`. Existing ticket records MUST be backfilled with an associated tenant. Guest ticket creation without an authenticated user MUST resolve and record the target `tenant` in the ticket record. The system MUST link `SupportMembership` to `Tenant` via a foreign key (`SupportMembership.tenant`), or associate it with the master tenant context if `tenant` is omitted or null for global support staff. The database model and serializer validation MUST reject ticket creation or modification if a specified `workspace` does not belong to the designated `tenant`.

#### Scenario: Ticket creation with explicit tenant and valid workspace
- GIVEN an authenticated user belonging to "Tenant Alpha"
- AND an active workspace "Workspace Alpha-1" belonging to "Tenant Alpha"
- WHEN the user submits a new ticket specifying "Workspace Alpha-1"
- THEN the ticket MUST be created with `tenant` referencing "Tenant Alpha"
- AND `ticket.workspace` MUST reference "Workspace Alpha-1".

#### Scenario: Ticket creation rejected when workspace does not belong to ticket tenant
- GIVEN an authenticated user or API client submitting a ticket for "Tenant Alpha"
- AND a workspace "Workspace Beta-1" belonging to "Tenant Beta"
- WHEN ticket validation is executed with `tenant` set to "Tenant Alpha" and `workspace` set to "Workspace Beta-1"
- THEN the system MUST reject the creation with a validation error
- AND no ticket record SHALL be persisted in the database.

#### Scenario: Guest ticket creation with resolved tenant
- GIVEN an unauthenticated guest user submitting a support request with valid guest contact details and a target tenant identifier
- WHEN the ticket creation endpoint processes the request
- THEN the system MUST resolve the target tenant from the request context or payload
- AND the ticket MUST be persisted with `tenant` set to the resolved tenant
- AND `ticket.user` MUST remain null.

#### Scenario: Support membership association with tenant
- GIVEN an administrative user registering a support member for "Tenant Alpha"
- WHEN a `SupportMembership` record is created with `role="support_agent"` and `tenant="Tenant Alpha"`
- THEN the `SupportMembership` MUST persist with the foreign key pointing to "Tenant Alpha"
- AND the member's support scope SHALL be restricted to "Tenant Alpha".

#### Scenario: Global master tenant support membership
- GIVEN a platform support staff member operating globally across tenants
- WHEN a `SupportMembership` record is created associated with the global master tenant (`is_global=True`)
- THEN the membership MUST designate platform-wide support authority across customer tenants.

### Requirement: Contextual Support Access Control
The system MUST protect all support API endpoints (`TicketViewSet`, `CommentViewSet`, `AttachmentViewSet`, `CommentAttachmentViewSet`, and `SupportMembershipViewSet`) with `HasContextualPermission`. Support viewsets MUST NOT return unfiltered querysets such as `Ticket.objects.all()`. In `TicketViewSet.get_queryset()`, tickets MUST be strictly filtered to return only tickets belonging to the request's active tenant (`request.tenant`), tickets explicitly assigned to the authenticated user (`assigned_to=request.user`), or all tickets if the user possesses global support manager or administrative privileges. Non-admin, non-assigned users from another tenant MUST receive an HTTP 404 Not Found or HTTP 403 Forbidden response when attempting to list, retrieve, update, or delete tickets outside their active tenant. Direct object-level operations and custom actions (`conversation`, `mark_as_read`, `delegate`) MUST verify contextual ownership or explicit technician assignment.

#### Scenario: Tenant user listing tickets returns only tickets belonging to active tenant
- GIVEN two tenants, "Tenant Alpha" and "Tenant Beta", each containing distinct tickets
- AND an authenticated user belonging to "Tenant Alpha" operating with active tenant context "Tenant Alpha"
- WHEN the user sends a `GET /api/v1/support/tickets/` request
- THEN the returned list MUST contain only tickets belonging to "Tenant Alpha"
- AND no tickets belonging to "Tenant Beta" SHALL be returned.

#### Scenario: Cross-tenant ticket retrieval denied for unauthorized user
- GIVEN a ticket "TICKET-B1" belonging to "Tenant Beta"
- AND an authenticated user belonging to "Tenant Alpha" who is NOT assigned to "TICKET-B1" and lacks global admin privileges
- WHEN the user attempts to retrieve the ticket via `GET /api/v1/support/tickets/{TICKET-B1-ID}/`
- THEN the system MUST reject the request with an HTTP 404 Not Found or HTTP 403 Forbidden response
- AND no ticket details SHALL be disclosed.

#### Scenario: Cross-tenant ticket retrieval permitted for assigned technician
- GIVEN a ticket "TICKET-B1" belonging to "Tenant Beta"
- AND a technician user "Tech-1" belonging to the master tenant who is explicitly assigned to "TICKET-B1" (`assigned_to=Tech-1`)
- WHEN "Tech-1" sends a `GET /api/v1/support/tickets/{TICKET-B1-ID}/` request
- THEN the system MUST evaluate the explicit assignment and permit the request
- AND the complete ticket payload MUST be returned.

#### Scenario: Ticket modification restricted by contextual permission
- GIVEN a ticket belonging to "Tenant Alpha"
- AND an authenticated user belonging to "Tenant Alpha" who lacks `change_ticket` permission
- WHEN the user attempts to update the ticket via `PATCH /api/v1/support/tickets/{id}/`
- THEN `HasContextualPermission` MUST deny the request with an HTTP 403 Forbidden response.

#### Scenario: Global support manager cross-tenant management
- GIVEN an authenticated user holding the `support_manager` role in the global master tenant (`is_global=True`)
- WHEN the support manager accesses ticket collections or detail endpoints across any customer tenant
- THEN the system MUST validate the user's global authority and permit the operation
- AND the system MUST allow cross-tenant ticket management and assignment.

### Requirement: Secure Comment and Attachment Scoping
The system MUST ensure that all comments (`Comment`), ticket attachments (`Attachment`), and comment attachments (`CommentAttachment`) strictly inherit their parent ticket's tenant isolation. `CommentViewSet`, `AttachmentViewSet`, and `CommentAttachmentViewSet` MUST enforce that any comment or attachment created, retrieved, or listed is bounded by the parent ticket's tenant context. In `CommentViewSet.get_queryset()`, comments MUST be strictly filtered such that users only access comments on tickets they are authorized to view. Submitting a comment or attachment referencing a ticket outside the user's active tenant and unassigned to the user MUST be rejected with HTTP 403 Forbidden or HTTP 404 Not Found. File attachment downloads and metadata endpoints MUST enforce contextual tenant checks matching the parent ticket.

#### Scenario: Comment creation inherits parent ticket tenant boundary
- GIVEN a ticket belonging to "Tenant Alpha"
- AND an authenticated user authorized within "Tenant Alpha"
- WHEN the user creates a comment on the ticket via `POST /api/v1/support/comments/`
- THEN the comment MUST be created and linked to the ticket
- AND the comment MUST be visible only within "Tenant Alpha" or to the technician assigned to the ticket.

#### Scenario: Comment creation rejected on unassigned cross-tenant ticket
- GIVEN a ticket belonging to "Tenant Beta"
- AND an authenticated user affiliated with "Tenant Alpha" who is NOT assigned to the ticket
- WHEN the user attempts to post a comment referencing the "Tenant Beta" ticket
- THEN the system MUST reject the request with an HTTP 403 Forbidden or HTTP 404 Not Found response
- AND no comment record SHALL be created.

#### Scenario: Comment listing strictly filtered by active tenant and assignments
- GIVEN comments belonging to tickets in "Tenant Alpha" and comments belonging to tickets in "Tenant Beta"
- AND an authenticated user operating with active tenant context "Tenant Alpha"
- WHEN the user requests `GET /api/v1/support/comments/`
- THEN the response MUST include only comments associated with tickets in "Tenant Alpha"
- AND comments associated with "Tenant Beta" tickets MUST NOT be returned.

#### Scenario: Attachment access inherits parent ticket tenant boundary
- GIVEN an attachment uploaded to a ticket belonging to "Tenant Beta"
- AND an authenticated user whose active tenant context is "Tenant Alpha" without assignment to the ticket
- WHEN the user attempts to retrieve the attachment metadata or file content
- THEN the system MUST deny the request with an HTTP 404 Not Found or HTTP 403 Forbidden response.

#### Scenario: Assigned technician access to ticket conversation and attachments
- GIVEN a ticket in "Tenant Beta" with multiple comments and file attachments
- AND a technician from the master tenant explicitly assigned to the ticket
- WHEN the technician calls the `conversation` action or retrieves attachments for the ticket
- THEN the system MUST authorize the request based on the ticket assignment
- AND the complete conversation tree with all comments and attachment metadata MUST be returned.

