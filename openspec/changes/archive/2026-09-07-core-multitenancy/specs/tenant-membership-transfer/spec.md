# Tenant Membership Transfer Specification

## Purpose
Defines the transactional lifecycle, authorization, permission cleanup, external service synchronization, and audit logging required to safely transfer user accounts between tenants without permission residue, orphaned resources, or state desynchronization.

## ADDED Requirements

### Requirement: Atomic User Tenant Transfer
The transfer of a user account from a source tenant to a destination tenant MUST be executed within a database atomic transaction (`transaction.atomic`). The system MUST validate pre-conditions before executing any modifications. If any stage of the transfer fails—including input validation, permission revocation, destination association, or external system synchronization—the entire transaction MUST roll back, restoring the user and all associated objects to their exact pre-transfer state.

#### Scenario: Successful atomic transfer of user between tenants
- GIVEN an active user currently affiliated with "Tenant Alpha"
- AND an active destination tenant "Tenant Beta" distinct from "Tenant Alpha"
- AND an authorized administrative user initiating the transfer request
- WHEN the transfer service is executed with the target user, source tenant, and destination tenant
- THEN the user's primary tenant assignment MUST be updated to "Tenant Beta"
- AND all revocation and reassignment operations MUST commit atomically.

#### Scenario: Rejection of transfer to identical tenant
- GIVEN a user currently affiliated with "Tenant Alpha"
- WHEN an administrator requests a transfer where both source and destination are "Tenant Alpha"
- THEN the system MUST reject the transfer request with a validation error
- AND no database or permission modifications SHALL occur.

#### Scenario: Rejection of transfer for non-existent destination tenant
- GIVEN a user affiliated with "Tenant Alpha"
- WHEN an administrator requests a transfer to a non-existent tenant ID
- THEN the system MUST reject the request with an HTTP 404 Not Found or validation error
- AND the user's affiliation with "Tenant Alpha" MUST remain unchanged.

#### Scenario: Transaction rollback upon unexpected failure during transfer
- GIVEN an ongoing transfer of a user from "Tenant Alpha" to "Tenant Beta"
- WHEN an unexpected database error or unhandled exception occurs during membership reassignment
- THEN the transaction MUST roll back entirely
- AND the user's tenant, workspace memberships, and permissions MUST remain identical to their pre-transfer state in "Tenant Alpha".

#### Scenario: Rejection of transfer by unauthorized initiator
- GIVEN a user affiliated with "Tenant Alpha"
- AND a request initiated by a user lacking global administrative or cross-tenant transfer authority
- WHEN the transfer request is received
- THEN the system MUST reject the operation with an HTTP 403 Forbidden response
- AND no changes SHALL be made.

### Requirement: Permission and Membership Revocation
During the tenant transfer process, the system MUST completely revoke and purge all permissions, memberships, and role assignments associated with the source tenant before establishing privileges in the destination tenant. No residual permissions, workspace memberships, or group affiliations from the source tenant SHALL persist.

#### Scenario: Purge of source tenant workspace memberships
- GIVEN a user who is a member of two workspaces in "Tenant Alpha" with assigned roles
- WHEN the user is transferred to "Tenant Beta"
- THEN all `WorkspaceMembership` records for the user in "Tenant Alpha" workspaces MUST be deleted
- AND the user MUST NOT retain any workspace membership in "Tenant Alpha".

#### Scenario: Removal of user from source tenant Django auth groups
- GIVEN a user who belongs to Django `Group`s created for roles in "Tenant Alpha" (such as `{role.id}_{role.name}_Tenant Alpha`)
- WHEN the user is transferred to "Tenant Beta"
- THEN the user MUST be removed from all such source tenant groups
- AND the user's `user.groups` relation MUST NOT contain any groups belonging to "Tenant Alpha".

#### Scenario: Removal of direct object-level permissions in source tenant
- GIVEN a user who has direct Django Guardian object permissions on workspaces, roles, or devices in "Tenant Alpha"
- WHEN the user is transferred to "Tenant Beta"
- THEN the system MUST revoke all direct object permissions for the user on objects belonging to "Tenant Alpha"
- AND querying permissions for the user on "Tenant Alpha" objects MUST return empty.

#### Scenario: Assignment to default workspace in destination tenant
- GIVEN a successful transfer of a user to "Tenant Beta"
- WHEN the transfer finalizes the user's setup in "Tenant Beta"
- THEN the system MUST assign the user to the default workspace of "Tenant Beta"
- AND the user MUST receive the default role (or "Sin rol") in that default workspace
- AND base user permissions for the new tenant MUST be initialized.

### Requirement: ChirpStack Consistency on Transfer
The transfer process MUST maintain state synchronization with external ChirpStack tenants. When a transferred user has an associated ChirpStack user record (`ApiUser` or ChirpStack user mapping), the user's association with the source ChirpStack tenant MUST be updated to the destination ChirpStack tenant. If the external ChirpStack API call fails, the system MUST handle the error according to the configured synchronization policy and record the error state.

#### Scenario: Successful synchronization of ChirpStack tenant association
- GIVEN a user with an active ChirpStack user account associated with source ChirpStack tenant ID `cs_source`
- AND a destination tenant having a valid ChirpStack tenant ID `cs_dest`
- WHEN the user tenant transfer is executed
- THEN the system MUST invoke the ChirpStack API to disassociate the user from `cs_source` and associate the user with `cs_dest`
- AND the local `ApiUser` record MUST update its workspace and tenant reference and set `sync_status` to `"SYNCED"`.

#### Scenario: Handling ChirpStack API failure during transfer
- GIVEN a user being transferred to "Tenant Beta" whose destination ChirpStack API call returns an HTTP 500 error or network timeout
- WHEN the external call fails during the transfer workflow
- THEN the system MUST record `sync_status="ERROR"` and store the error description in `sync_error`
- AND the system MUST log the failure with error details for operational retry/reconciliation
- AND the local database state MUST remain consistent without orphaned partial state.

#### Scenario: Transfer of user without ChirpStack account
- GIVEN a user who does not have an associated ChirpStack user account or devices
- WHEN the tenant transfer is executed
- THEN the ChirpStack synchronization step MUST be bypassed cleanly without raising an error
- AND the transfer MUST complete successfully.

### Requirement: Audit Logging of Tenant Transfer
The system MUST record an immutable audit log entry for every tenant transfer operation using the platform audit logging framework (`django-auditlog`). The audit log MUST capture complete provenance details, enabling compliance verification and historical tracking of tenant migrations.

#### Scenario: Detailed audit log entry created upon successful transfer
- GIVEN an administrator "admin_user" transferring target user "jane_doe" from "Tenant Alpha" to "Tenant Beta"
- WHEN the transfer operation successfully commits
- THEN an audit log entry MUST be created in `django-auditlog`
- AND the entry MUST record:
  - The target user instance (`User: jane_doe`)
  - The source tenant ID and name (`Tenant Alpha`)
  - The destination tenant ID and name (`Tenant Beta`)
  - The actor/initiator ID and username (`admin_user`)
  - The exact timestamp of the transfer
  - The action type indicating a tenant membership transfer.

#### Scenario: Immutability and traceability of transfer log records
- GIVEN an existing audit log entry recording a past tenant transfer
- WHEN any user or administrator queries the audit log endpoint
- THEN the log record MUST be accessible to authorized compliance/admin users in read-only mode
- AND the log record MUST NOT be editable or deletable through standard API endpoints.
