# cross-tenant-technician-dispatch Specification

## Purpose
Defines the Hybrid Cross-Tenant Technician Dispatch architecture for `Monitor_Atlas`. This specification enables support technicians (typically originating from a central master tenant) to troubleshoot, manage, and resolve support tickets submitted by customer tenants without compromising tenant isolation boundaries. It specifies default ticket-scoped cross-tenant access, formal TTL-bounded temporary diagnostic workspace passes (`TechnicianAssignment`), automatic and administrative pass lifecycle enforcement, and complete audit logging across all delegation and pass management actions.

## ADDED Requirements

### Requirement: Ticket-Scoped Cross-Tenant Delegation
The system MUST allow support managers and platform administrators to delegate or assign a ticket belonging to any customer tenant to an authenticated technician (`ticket.assigned_to = technician`), regardless of the technician's home tenant. The assigned technician MUST be granted authorization to view, update classification attributes (such as status and priority), add comments, and upload attachments to that specific ticket without requiring membership or roles in the customer tenant or workspace. The technician's access privileges SHALL be strictly confined to the assigned ticket; assigning a technician to a ticket MUST NOT grant broader access to other customer tickets, workspaces, devices, or tenant assets. When a ticket is reassigned or unassigned, the previously assigned technician's ticket-level access MUST immediately terminate.

#### Scenario: Support manager delegates cross-tenant ticket to technician
- GIVEN a ticket submitted by a customer user belonging to "Tenant Alpha"
- AND an authenticated support manager affiliated with the global master tenant
- AND a technician user "Tech-Dave" affiliated with the global master tenant
- WHEN the support manager executes the `delegate` action on the ticket with `assigned_to_id` referencing "Tech-Dave"
- THEN the ticket's `assigned_to` attribute MUST be updated to "Tech-Dave"
- AND a notification MUST be sent to "Tech-Dave"
- AND "Tech-Dave" MUST now be authorized to retrieve and update the ticket.

#### Scenario: Assigned technician accesses and updates customer ticket
- GIVEN a ticket belonging to "Tenant Alpha" with `assigned_to` set to technician "Tech-Dave"
- AND "Tech-Dave" holds no membership or assigned roles within "Tenant Alpha"
- WHEN "Tech-Dave" sends a `GET /api/v1/support/tickets/{id}/` or `PATCH /api/v1/support/tickets/{id}/` request to update status to "in_progress"
- THEN the system MUST evaluate the ticket assignment and permit the request
- AND the ticket status update MUST be persisted successfully.

#### Scenario: Assigned technician access strictly confined to assigned ticket
- GIVEN technician "Tech-Dave" assigned to ticket "Ticket-1" in "Tenant Alpha"
- AND "Tenant Alpha" contains another ticket "Ticket-2" assigned to a different technician
- WHEN "Tech-Dave" attempts to retrieve `GET /api/v1/support/tickets/Ticket-2/`
- THEN the system MUST deny access with an HTTP 404 Not Found or HTTP 403 Forbidden response
- AND no data for "Ticket-2" SHALL be disclosed.

#### Scenario: Ticket access revocation upon reassignment or unassignment
- GIVEN technician "Tech-Dave" assigned to ticket "Ticket-1" in "Tenant Alpha"
- WHEN an authorized support manager reassigns "Ticket-1" to technician "Tech-Sarah"
- THEN "Tech-Dave" MUST no longer be authorized to access "Ticket-1"
- AND any subsequent update attempt by "Tech-Dave" on "Ticket-1" MUST be rejected with an HTTP 403 Forbidden response.

### Requirement: Temporary Diagnostic Workspace Pass
The system MUST provide a `TechnicianAssignment` model representing a temporary diagnostic workspace pass for in-depth troubleshooting. Each pass MUST record the assigned technician (`technician`), the associated ticket (`ticket`), the customer workspace (`workspace`), the authorizing administrator (`granted_by`), the creation timestamp (`granted_at`), the expiration timestamp (`expires_at`), the status (`status`, supporting choices `active`, `expired`, `revoked`), and the troubleshooting justification (`reason`). Only authorized support managers or administrators MUST be permitted to issue a diagnostic pass. While a pass is `active` and within its TTL window, `HasContextualPermission` MUST grant the designated technician read/diagnostic access to the customer workspace resources (such as devices, gateways, machines, and measurements). The diagnostic pass MUST NOT grant permission to perform destructive or mutating operations on customer resources unless explicitly authorized.

#### Scenario: Support manager issues diagnostic pass with TTL
- GIVEN an open ticket in "Tenant Alpha" linked to "Workspace Alpha-Production"
- AND a technician "Tech-Dave" assigned to the ticket
- AND an authenticated support manager
- WHEN the support manager creates a `TechnicianAssignment` for "Tech-Dave" on "Workspace Alpha-Production" with a 4-hour TTL and reason "Diagnosing intermittent sensor stream"
- THEN the system MUST create the `TechnicianAssignment` with `status="active"`
- AND `expires_at` MUST be calculated and set to current time plus 4 hours
- AND `granted_by` MUST reference the authorizing support manager.

#### Scenario: Active diagnostic pass permits read-only workspace telemetry and device access
- GIVEN an active `TechnicianAssignment` pass issued to technician "Tech-Dave" for "Workspace Alpha-Production"
- WHEN "Tech-Dave" sends a `GET /api/v1/infrastructure/devices/` request with `X-Workspace-ID: Workspace Alpha-Production`
- THEN `HasContextualPermission` MUST recognize the valid active pass
- AND the system MUST permit retrieval of device resources in "Workspace Alpha-Production".

#### Scenario: Diagnostic pass denies destructive mutations on workspace resources
- GIVEN an active `TechnicianAssignment` pass issued to technician "Tech-Dave" for "Workspace Alpha-Production"
- WHEN "Tech-Dave" attempts to delete a device via `DELETE /api/v1/infrastructure/devices/{device-id}/` in "Workspace Alpha-Production"
- THEN the system MUST reject the request with an HTTP 403 Forbidden response
- AND the diagnostic pass MUST NOT confer deletion or destruction permissions.

#### Scenario: Pass creation rejected for unauthorized user
- GIVEN a regular tenant user or technician without support manager privileges
- WHEN the user attempts to create a `TechnicianAssignment` diagnostic pass
- THEN the system MUST reject the request with an HTTP 403 Forbidden response
- AND no diagnostic pass SHALL be created.

### Requirement: Pass Lifecycle and Expiration Enforcement
The system MUST enforce pass validity at request evaluation time. A diagnostic pass SHALL be considered valid if and only if `status == 'active'` AND `now() < expires_at`. When the pass duration reaches or exceeds its expiration timestamp (`now() >= expires_at`), the pass MUST automatically be treated as expired, and all contextual diagnostic access to the customer workspace MUST immediately cease. Support managers, administrators, or the granting authority MUST have the ability to explicitly revoke an active pass at any time by updating `status` to `revoked`. Furthermore, when a ticket is transitioned to `resolved` or `closed` status, any active `TechnicianAssignment` passes associated with that ticket MUST automatically be terminated to prevent dangling access. Re-activating an expired or revoked pass MUST be prohibited.

#### Scenario: Automatic access denial upon TTL expiration
- GIVEN a `TechnicianAssignment` pass issued to "Tech-Dave" on "Workspace Alpha-Production" where `expires_at` is earlier than current time
- WHEN "Tech-Dave" sends a diagnostic request to "Workspace Alpha-Production"
- THEN `HasContextualPermission` MUST evaluate the expiration condition
- AND the system MUST reject the request with an HTTP 403 Forbidden response.

#### Scenario: Administrative revocation of active pass
- GIVEN an active `TechnicianAssignment` pass issued to "Tech-Dave"
- WHEN an authorized administrator invokes the revocation endpoint for the pass
- THEN the pass `status` MUST be updated to `revoked`
- AND all subsequent requests from "Tech-Dave" attempting to access the workspace via the pass MUST be rejected with HTTP 403 Forbidden.

#### Scenario: Automatic pass revocation upon ticket resolution or closure
- GIVEN a ticket with an associated active `TechnicianAssignment` pass
- WHEN the ticket status is updated to "resolved" or "closed"
- THEN the system MUST automatically set the associated pass `status` to `revoked`
- AND the technician's workspace diagnostic access MUST terminate immediately.

#### Scenario: Re-activation of expired or revoked pass prohibited
- GIVEN a `TechnicianAssignment` pass with `status` set to "expired" or "revoked"
- WHEN an API client or user attempts to mutate the pass status back to "active"
- THEN the system MUST reject the operation with a validation error
- AND the pass MUST remain invalid.

### Requirement: Audit Logging and Delegation Traceability
The system MUST record comprehensive audit log entries for all ticket delegation events, technician assignments, diagnostic pass issuances, revocations, and expirations using `django-auditlog`. The `TechnicianAssignment` model MUST be registered with the audit log subsystem. Every ticket delegation event MUST record the acting user, target ticket, previous assignee, new assignee, and timestamp. Every diagnostic pass issuance MUST record the granting authority, technician, target tenant and workspace, TTL duration, reason, and pass identifier. Every pass revocation or automated closure MUST record the trigger (actor or ticket status change), the pass identifier, and the timestamp. All generated audit logs MUST be immutable and accessible to administrators for compliance auditing.

#### Scenario: Audit logging for ticket delegation
- GIVEN an authenticated support manager "Manager-Bob"
- WHEN "Manager-Bob" delegates ticket "Ticket-1" to technician "Tech-Dave"
- THEN an audit log entry in `LogEntry` MUST be created
- AND the entry MUST record "Manager-Bob" as the actor, "Ticket-1" as the target object, and log the change in `assigned_to`.

#### Scenario: Audit logging for diagnostic pass issuance
- GIVEN an authorized support manager issuing a `TechnicianAssignment` pass
- WHEN the pass is saved to the database
- THEN an audit log entry MUST be created for the `TechnicianAssignment` instance
- AND the entry MUST record the authorizer, technician, target workspace, and pass expiration time.

#### Scenario: Audit logging for pass revocation
- GIVEN an active `TechnicianAssignment` pass
- WHEN an administrator revokes the pass
- THEN an audit log entry MUST be created recording the status change to "revoked", the revoking user, and the revocation timestamp.

#### Scenario: Audit logging for automated pass closure upon ticket resolution
- GIVEN an active `TechnicianAssignment` pass linked to an open ticket
- WHEN the ticket is resolved, triggering automated pass revocation
- THEN the audit logging engine MUST capture the pass status transition to "revoked"
- AND the audit entry MUST record the automated ticket resolution trigger.
