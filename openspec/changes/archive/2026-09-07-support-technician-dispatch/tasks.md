# Tasks: Support Technician Dispatch

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

## Phase 1: Support Data Models & Database Migrations

- [x] **1.1 Add `tenant` and `workspace` foreign keys to `Ticket` and `SupportMembership` in `Monitor_Atlas/support/models.py`**
  - Add non-nullable foreign key `tenant` to `Ticket` in `Monitor_Atlas/support/models.py` referencing `organizations.Tenant` (`on_delete=models.CASCADE`, `related_name="tickets"`).
  - Add optional foreign key `workspace` to `Ticket` in `Monitor_Atlas/support/models.py` referencing `organizations.Workspace` (`null=True`, `blank=True`, `on_delete=models.SET_NULL`, `related_name="tickets"`).
  - Update `Ticket.clean()` in `Monitor_Atlas/support/models.py` to enforce that if `workspace` is specified, `workspace.tenant_id == self.tenant_id`.
  - Update `TicketSerializer` in `Monitor_Atlas/support/serializers.py` to validate that the provided `workspace` belongs to the designated `tenant`.
  - Add nullable foreign key `tenant` to `SupportMembership` in `Monitor_Atlas/support/models.py` referencing `organizations.Tenant` (`null=True`, `blank=True`, `on_delete=models.CASCADE`, `related_name="support_memberships"`), where `null` designates global master-tenant support authority.
  - Update `SupportMembershipSerializer` in `Monitor_Atlas/support/serializers.py` to expose and validate `tenant`.

- [x] **1.2 Implement `TechnicianAssignment` model with TTL and `is_valid()` in `Monitor_Atlas/support/models.py` and register with `auditlog`**
  - Define `TechnicianAssignment` model in `Monitor_Atlas/support/models.py` with fields:
    - `id`: `models.CharField(max_length=16, primary_key=True, default=generate_id, editable=False)`
    - `technician`: `models.ForeignKey(User, on_delete=models.CASCADE, related_name="technician_assignments")`
    - `ticket`: `models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="technician_assignments")`
    - `workspace`: `models.ForeignKey('organizations.Workspace', on_delete=models.CASCADE, related_name="technician_assignments")`
    - `granted_by`: `models.ForeignKey(User, on_delete=models.CASCADE, related_name="granted_technician_assignments")`
    - `granted_at`: `models.DateTimeField(auto_now_add=True)`
    - `expires_at`: `models.DateTimeField()`
    - `status`: `models.CharField(max_length=20, choices=[("active", "Active"), ("expired", "Expired"), ("revoked", "Revoked")], default="active")`
    - `reason`: `models.TextField()`
  - Implement helper method `is_valid(self)` on `TechnicianAssignment` in `Monitor_Atlas/support/models.py` returning `self.status == "active" and timezone.now() < self.expires_at`.
  - Implement `clean()` validation on `TechnicianAssignment` in `Monitor_Atlas/support/models.py` prohibiting re-activation of expired or revoked passes.
  - Register `TechnicianAssignment` with `auditlog.registry.auditlog` in `Monitor_Atlas/support/models.py`.
  - Define `TechnicianAssignmentSerializer` in `Monitor_Atlas/support/serializers.py` serializing assignment metadata and pass validity state.

- [x] **1.3 Create and run database migrations in `Monitor_Atlas/support/migrations/`**
  - Create database migration in `Monitor_Atlas/support/migrations/0004_support_multitenancy_dispatch.py`.
  - Add schema operations for `Ticket.tenant`, `Ticket.workspace`, `SupportMembership.tenant`, and create model `TechnicianAssignment`.
  - Implement data migration logic within the migration to backfill existing tickets with the ticket user's tenant or the global master tenant (`Tenant.objects.filter(is_global=True).first()`).
  - Set `tenant` on `Ticket` as non-nullable after the backfill step completes.
  - Apply migrations to the test/development database and verify constraints.

---

## Phase 2: Contextual Permission Evaluator Integration

- [x] **2.1 Update `has_contextual_perm()` in `Monitor_Atlas/roles/permissions.py` to grant read-only access to infrastructure when a technician holds an active, valid `TechnicianAssignment`**
  - Update `has_contextual_perm()` in `Monitor_Atlas/roles/permissions.py` to inspect `TechnicianAssignment` records when evaluating workspace-level permissions.
  - Identify read-only diagnostic permissions matching safe methods (e.g., `view_device`, `view_machine`, `view_gateway`, `view_application`, `view_measurement`, `view_location`).
  - Query `TechnicianAssignment` for active, unexpired passes matching `technician=user`, `workspace=workspace`, `status="active"`, and `expires_at > timezone.now()`.
  - If a valid `TechnicianAssignment` is found and the requested permission is a read-only safe action, grant access (`return True`).
  - Ensure mutating or destructive permissions (`add_*`, `change_*`, `delete_*`) reject access unless explicit separate administrative or workspace permissions exist.
  - Ensure requests where `timezone.now() >= expires_at` or `status != "active"` are denied without bypass.

- [x] **2.2 Update `get_object_workspace_and_tenant()` in `Monitor_Atlas/roles/permissions.py` to resolve boundaries for `Ticket` and `Comment`**
  - Update `get_object_workspace_and_tenant()` in `Monitor_Atlas/roles/permissions.py` to recognize support subsystem domain models.
  - For `Ticket` objects: resolve `workspace = obj.workspace` and `tenant = obj.tenant`.
  - For `Comment` objects: resolve `workspace = obj.ticket.workspace` and `tenant = obj.ticket.tenant`.
  - For `Attachment` objects: resolve `workspace = obj.ticket.workspace` and `tenant = obj.ticket.tenant`.
  - For `CommentAttachment` objects: resolve `workspace = obj.comment.ticket.workspace` and `tenant = obj.comment.ticket.tenant`.
  - For `TechnicianAssignment` objects: resolve `workspace = obj.workspace` and `tenant = obj.workspace.tenant` (or `obj.ticket.tenant`).
  - Retain fallback handling for legacy tickets with `obj.organization` to prevent regressions during rollout.

---

## Phase 3: Support ViewSets Access Control & Dispatch Actions

- [x] **3.1 Secure `TicketViewSet` and `CommentViewSet` in `Monitor_Atlas/support/views.py` with `HasContextualPermission` and tenant/technician queryset scoping**
  - Update `TicketViewSet` in `Monitor_Atlas/support/views.py`:
    - Add `permission_classes = [IsAuthenticated, HasContextualPermission]` and set `scope = "ticket"`.
    - Override `get_queryset()` to filter tickets strictly by active tenant (`tenant=request.tenant`) or technician assignment (`assigned_to=request.user`), with bypass for global support managers and superusers.
    - Ensure detail actions (`conversation`, `mark_as_read`, `retrieve`) verify contextual boundary or technician assignment.
  - Update `CommentViewSet` in `Monitor_Atlas/support/views.py`:
    - Add `permission_classes = [IsAuthenticated, HasContextualPermission]` and set `scope = "comment"`.
    - Override `get_queryset()` to return comments where parent ticket matches `Q(ticket__tenant=request.tenant) | Q(ticket__assigned_to=request.user)` (or all comments for global support managers/superusers).
  - Update `AttachmentViewSet` (`scope = "attachment"`), `CommentAttachmentViewSet` (`scope = "commentattachment"`), and `SupportMembershipViewSet` (`scope = "supportmembership"`) in `Monitor_Atlas/support/views.py` with `HasContextualPermission` and tenant boundary scoping.

- [x] **3.2 Update `perform_create()` in `Monitor_Atlas/support/views.py` to bind tickets to `request.tenant` and resolve master tenant support managers**
  - Update `TicketViewSet.perform_create()` in `Monitor_Atlas/support/views.py` to bind `ticket.tenant` from `request.tenant` for authenticated users.
  - Resolve tenant context for unauthenticated guest tickets based on guest request context or payload tenant identifier.
  - Update support manager query to select support managers from the global master tenant (`SupportMembership.objects.filter(role="support_manager", tenant__is_global=True).first()` or `SupportMembership.objects.filter(role="support_manager").first()`).
  - Assign newly created tickets to the resolved master tenant support manager.
  - Preserve automated creation of JWT access tokens and notification emails to user and staff.

- [x] **3.3 Implement `delegate`, `grant_diagnostic_pass`, and `revoke_diagnostic_pass` actions on `TicketViewSet` in `Monitor_Atlas/support/views.py` with `auditlog` logging and automated pass revocation upon ticket closure**
  - Refactor `@action(detail=True, methods=["post"])` `delegate` on `TicketViewSet` in `Monitor_Atlas/support/views.py`:
    - Validate `assigned_to_id` in payload, assign ticket to technician, reset `is_read=False`, and emit notification via `NotificationsEngine`.
    - Record audit log entry in `auditlog.models.LogEntry` logging ticket delegation details (actor, target ticket, previous assignee, new assignee).
  - Add `@action(detail=True, methods=["post"])` `grant_diagnostic_pass` on `TicketViewSet` in `Monitor_Atlas/support/views.py`:
    - Restrict invocation to support managers and administrators.
    - Validate `technician_id`, `workspace_id`, `duration_hours`, and `reason` from payload.
    - Verify that target `workspace` belongs to `ticket.tenant`.
    - Create `TechnicianAssignment` instance with `expires_at = timezone.now() + timedelta(hours=duration_hours)` and `status="active"`.
    - Return serialized pass data with HTTP 201 Created.
  - Add `@action(detail=True, methods=["post"])` `revoke_diagnostic_pass` on `TicketViewSet` in `Monitor_Atlas/support/views.py`:
    - Accept `pass_id` from payload, locate `TechnicianAssignment`, update status to `"revoked"`, and return HTTP 200 OK.
  - Update `perform_update()` / `partial_update()` on `TicketViewSet` in `Monitor_Atlas/support/views.py`:
    - Detect when `ticket.status` transitions to `"resolved"` or `"closed"`.
    - Query and update all active `TechnicianAssignment` passes associated with the ticket to `status="revoked"`.
    - Record audit log entry documenting automated pass revocation triggered by ticket resolution/closure.

---

## Phase 4: Automated Testing & Verification

- [x] **4.1 Unit and integration tests for support multitenancy in `Monitor_Atlas/tests/test_support_multitenancy.py`**
  - Create test suite `Monitor_Atlas/tests/test_support_multitenancy.py` testing support tenant isolation.
  - Test `Ticket` model validation rejects ticket creation when `workspace` does not belong to `ticket.tenant`.
  - Test guest ticket creation resolves and associates target tenant.
  - Test `SupportMembership` tenant association and global master-tenant support membership scoping.
  - Test `TicketViewSet.get_queryset()` returns only active tenant tickets and denies cross-tenant listing.
  - Test retrieving or updating a ticket from another tenant returns HTTP 403 Forbidden or HTTP 404 Not Found.
  - Test `CommentViewSet`, `AttachmentViewSet`, and `CommentAttachmentViewSet` strictly inherit parent ticket tenant boundary and block cross-tenant leakage.
  - Test global support manager can view and manage tickets across customer tenants.

- [x] **4.2 Integration tests for technician cross-tenant delegation and diagnostic pass lifecycle in `Monitor_Atlas/tests/test_technician_dispatch.py`**
  - Create test suite `Monitor_Atlas/tests/test_technician_dispatch.py` testing hybrid technician dispatch and diagnostic passes.
  - Test ticket delegation (`POST /api/v1/support/tickets/{id}/delegate/`) assigns technician and logs audit trail.
  - Test assigned master tenant technician can retrieve, comment on, and update assigned customer ticket without tenant membership.
  - Test assigned technician is denied access to other unassigned customer tickets in the same tenant.
  - Test reassigning ticket to another technician immediately terminates previous technician's access.
  - Test support manager issues `TechnicianAssignment` via `POST /api/v1/support/tickets/{id}/grant_diagnostic_pass/`.
  - Test active diagnostic pass grants read-only access to customer workspace infrastructure (`GET /api/v1/infrastructure/devices/`, `view_device`).
  - Test diagnostic pass rejects mutating/destructive operations (`DELETE /api/v1/infrastructure/devices/{id}/`, `delete_device`).
  - Test expired pass (`timezone.now() >= expires_at`) immediately denies workspace access.
  - Test administrative revocation (`POST /api/v1/support/tickets/{id}/revoke_diagnostic_pass/`) terminates pass access.
  - Test ticket transition to `resolved` or `closed` automatically revokes associated active diagnostic passes.
  - Test comprehensive audit logging across ticket delegation, pass grant, and pass revocation lifecycles.
