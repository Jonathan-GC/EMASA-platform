from datetime import timedelta
from django.db import models
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from auditlog.models import LogEntry
from django.contrib.contenttypes.models import ContentType

from roles.permissions import HasContextualPermission
from .models import (
    Ticket,
    Comment,
    Attachment,
    CommentAttachment,
    SupportMembership,
    TechnicianAssignment,
)
from .serializers import (
    TicketSerializer,
    CommentSerializer,
    AttachmentSerializer,
    CommentAttachmentSerializer,
    SupportMembershipSerializer,
    TicketConversationSerializer,
    TechnicianAssignmentSerializer,
)

from users.models import User

from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiExample
from rest_framework.response import Response
from platform_backend.audit_mixins import AuditActionMixin, _current_audit_context

from .models import (
    PRIORITY_CHOICES,
    STATUS_CHOICES,
    CATEGORY_CHOICES,
    MACHINE_TYPE_CHOICES,
    ELECTRIC_MACHINE_CHOICES,
    MECHANICAL_MACHINE_CHOICES,
    INFRASTRUCTURE_CATEGORY_CHOICES,
    SUPPORT_MEMBERSHIP_ROLE_CHOICES,
)

from roles.helpers import support_manager_can_view_all_support_members

from users.emails import (
    send_ticket_created_notification_email,
    send_ticket_updated_notification_email,
    send_ticket_updated_notification_email_to_staff,
    send_new_ticket_notification_email_to_staff,
)

from users.jwt import generate_token

from .helpers import is_support_member
from notifications.engine import NotificationsEngine


def is_global_support_manager(user):
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return SupportMembership.objects.filter(
        user=user, role="support_manager"
    ).filter(models.Q(tenant__is_global=True) | models.Q(tenant__isnull=True)).exists()


def is_admin_or_support_manager(user):
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    from roles.helpers import get_global_admin_role_group
    global_group = get_global_admin_role_group()
    if (global_group and global_group in user.groups.all()) or user.groups.filter(name="global_admin").exists():
        return True
    return is_global_support_manager(user) or SupportMembership.objects.filter(user=user, role="support_manager").exists()


@extend_schema_view(
    list=extend_schema(description="Ticket List"),
    create=extend_schema(description="Ticket Create"),
    retrieve=extend_schema(description="Ticket Retrieve"),
    update=extend_schema(description="Ticket Update"),
    partial_update=extend_schema(description="Ticket Partial Update"),
    destroy=extend_schema(description="Ticket Destroy"),
    get_all_types=extend_schema(description="Get all classification types"),
    get_support_members=extend_schema(description="Get support members"),
    delegate=extend_schema(
        description="Delegate the ticket",
        examples=[
            OpenApiExample(
                "Delegate Ticket Example",
                summary="Delegate Ticket Example",
                description="Example payload for delegating a ticket to a support member.",
                value={"assigned_to_id": 2},
                request_only=True,
                response_only=False,
            ),
        ],
    ),
)
class TicketViewSet(AuditActionMixin, viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated, HasContextualPermission]
    scope = "ticket"

    def get_permissions(self):
        if self.action == "create" and not (self.request.user and self.request.user.is_authenticated):
            return []
        return [IsAuthenticated(), HasContextualPermission()]

    def get_queryset(self):
        user = self.request.user
        if not user or not user.is_authenticated:
            return Ticket.objects.none()

        if user.is_superuser or is_global_support_manager(user):
            return Ticket.objects.all()

        tenant = getattr(self.request, "tenant", getattr(user, "tenant", None))

        is_technician = SupportMembership.objects.filter(
            user=user, role__in=["technician", "support_agent"]
        ).exists()

        if is_technician:
            if tenant:
                return Ticket.objects.filter(models.Q(assigned_to=user) | models.Q(tenant=tenant))
            return Ticket.objects.filter(assigned_to=user)

        from roles.models import WorkspaceMembership
        is_tenant_admin = False
        if tenant:
            is_tenant_admin = WorkspaceMembership.objects.filter(
                user=user, workspace__tenant=tenant
            ).filter(models.Q(role__is_admin=True) | models.Q(role__name__icontains="admin")).exists()

        if is_tenant_admin:
            return Ticket.objects.filter(tenant=tenant)
        else:
            return Ticket.objects.filter(tenant=tenant, user=user)

    def perform_create(self, serializer):
        support_member = (
            SupportMembership.objects.filter(role="support_manager", tenant__is_global=True).first()
            or SupportMembership.objects.filter(role="support_manager", tenant__isnull=True).first()
            or SupportMembership.objects.filter(role="support_manager").first()
        )
        if not support_member:
            logger.error(
                "No support member with role 'support_manager' found. If in development, please run initial setup."
            )
            raise Exception(
                "Support manager not found. If in development, please run initial setup."
            )
        assigned_user = support_member.user

        # Resolve tenant
        resolved_tenant = None
        if self.request.user and self.request.user.is_authenticated:
            resolved_tenant = getattr(self.request, "tenant", getattr(self.request.user, "tenant", None))

        if not resolved_tenant:
            from organizations.models import Tenant
            tenant_id = (
                self.request.data.get("tenant")
                or self.request.data.get("tenant_id")
                or (self.request.headers.get("X-Tenant-ID") if hasattr(self.request, "headers") else None)
            )
            if tenant_id:
                resolved_tenant = Tenant.objects.filter(id=tenant_id).first()
            if not resolved_tenant and hasattr(self.request, "tenant"):
                resolved_tenant = self.request.tenant

        extra_kwargs = {"assigned_to": assigned_user}
        if resolved_tenant:
            extra_kwargs["tenant"] = resolved_tenant
        if self.request.user and self.request.user.is_authenticated:
            if not serializer.validated_data.get("user"):
                extra_kwargs["user"] = self.request.user

        ticket = serializer.save(**extra_kwargs)
        ticket_number = f"TICKET-{ticket.id}"
        if ticket.organization:
            ticket_body = f"{ticket.organization} submitted a Ticket."
        else:
            ticket_body = f"Ticket {ticket_number} has been submitted."

        NotificationsEngine.send_notification(
            users=[assigned_user],
            title="New Ticket Submitted",
            message=ticket_body,
            type="warning",
            topic="updates",
        )

        if not ticket.user_id:
            token = generate_token(
                scope="ticket_access",
                expires_minutes=60 * 24 * 3,
                ticket_id=str(ticket.id),
            )  # 3 days validity
            ticket_user_name = ticket.guest_name
            ticket_user_email = ticket.guest_email
        else:
            token = generate_token(
                user_id=ticket.user_id,
                scope="ticket_access",
                expires_minutes=60 * 24 * 3,
                ticket_id=str(ticket.id),
            )  # 3 days validity
            ticket_user = User.objects.get(id=ticket.user_id)
            ticket_user_name = ticket_user.get_full_name() or ticket_user.username
            ticket_user_email = ticket_user.email

        send_ticket_created_notification_email(
            name=ticket_user_name,
            email=ticket_user_email,
            ticket=ticket,
            token=token,
        )

        send_new_ticket_notification_email_to_staff(
            staff_email=assigned_user.email,
            ticket=ticket,
            comment=None,
        )

        return ticket

    def perform_update(self, serializer):
        ticket = serializer.save()
        if (ticket.status or "").lower() in ["resolved", "closed"]:
            active_passes = ticket.diagnostic_passes.filter(status__in=["ACTIVE", "active"])
            for pass_obj in active_passes:
                token = _current_audit_context.set({
                    "action_detail": "auto_revocation_on_ticket_closure",
                    "actor": self.request.user if (self.request.user and self.request.user.is_authenticated) else None,
                    "ticket_id": str(ticket.id),
                    "ticket_status": ticket.status,
                })
                try:
                    pass_obj.status = "REVOKED"
                    pass_obj.save()
                finally:
                    _current_audit_context.reset(token)
        return ticket

    @action(detail=True, methods=["get"], description="Get ticket conversation")
    def conversation(self, request, pk=None):
        """
        Returns the complete conversation for a ticket including:
        - Ticket details
        - All ticket attachments
        - All comments (ordered chronologically) with their attachments
        - The 'response' flag in each comment indicates if it's from the technician (True) or user (False)
        """
        ticket = self.get_object()

        ticket = Ticket.objects.prefetch_related(
            "attachments", "comments__attachments", "comments__user"
        ).get(pk=ticket.pk)

        serializer = TicketConversationSerializer(ticket)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], description="Mark ticket as read")
    def mark_as_read(self, request, pk=None):
        ticket = self.get_object()
        user = request.user

        if user and not is_support_member(user):
            logger.debug("user is not a support member")
            return Response({"not_modified": "no need to mark as read"}, status=204)
        elif user and ticket.assigned_to.id != user.id:
            logger.debug("user is not assigned to the ticket")
            return Response({"not_modified": "no need to mark as read"}, status=204)
        elif not user:
            logger.debug("no user associated with the request")
            return Response({"not_modified": "no need to mark as read"}, status=204)
        ticket.is_read = True
        ticket.save()
        return Response({"status": "ticket_marked_as_read"}, status=200)

    @action(detail=True, methods=["post"], description="Delegate the ticket")
    def delegate(self, request, pk=None):
        ticket = self.get_object()
        if not is_admin_or_support_manager(request.user):
            return Response(
                {"error": "Only administrators and support managers can delegate tickets."},
                status=status.HTTP_403_FORBIDDEN,
            )

        assigned_to_id = request.data.get("assigned_to_id")
        if not assigned_to_id:
            return Response({"error": "assigned_to_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            assigned_user = User.objects.get(id=assigned_to_id)
            prev_assigned = ticket.assigned_to

            token = _current_audit_context.set({
                "action_detail": "ticket_delegated",
                "actor": request.user,
                "previous_assignee": str(prev_assigned.id) if prev_assigned else None,
                "new_assignee": str(assigned_user.id),
            })
            try:
                ticket.assigned_to = assigned_user
                ticket.is_read = False
                ticket.save()
            finally:
                _current_audit_context.reset(token)

            NotificationsEngine.send_notification(
                users=[assigned_user],
                title="New Ticket Assignment",
                message=f"The ticket '{ticket.title}' has been delegated to you.",
                type="info",
                topic="updates",
            )
            return Response({"status": "ticket_delegated"}, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=["post"], description="Grant diagnostic pass for customer workspace")
    def grant_diagnostic_pass(self, request, pk=None):
        ticket = self.get_object()
        if not is_admin_or_support_manager(request.user):
            return Response(
                {"error": "Only support managers and administrators can grant diagnostic passes."},
                status=status.HTTP_403_FORBIDDEN,
            )

        technician_id = request.data.get("technician_id")
        workspace_id = request.data.get("workspace_id")
        duration_hours = request.data.get("duration_hours", 4)
        reason = request.data.get("reason", "")

        if not technician_id or not workspace_id:
            return Response(
                {"error": "technician_id and workspace_id are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            duration_hours = int(duration_hours)
        except (ValueError, TypeError):
            return Response(
                {"error": "duration_hours must be a valid integer."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        technician = User.objects.filter(id=technician_id).first()
        if not technician:
            return Response({"error": "Technician not found."}, status=status.HTTP_404_NOT_FOUND)

        from organizations.models import Workspace
        workspace = Workspace.objects.filter(id=workspace_id).first()
        if not workspace:
            return Response({"error": "Workspace not found."}, status=status.HTTP_404_NOT_FOUND)

        if ticket.tenant and workspace.tenant_id != ticket.tenant_id:
            return Response(
                {"error": "Target workspace does not belong to the ticket's tenant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        expires_at = timezone.now() + timedelta(hours=duration_hours)
        token = _current_audit_context.set({
            "action_detail": "grant_diagnostic_pass",
            "actor": request.user,
            "ticket_id": str(ticket.id),
            "technician_id": str(technician.id),
            "workspace_id": str(workspace.id),
            "duration_hours": duration_hours,
            "expires_at": expires_at.isoformat(),
        })
        try:
            assignment = TechnicianAssignment.objects.create(
                technician=technician,
                ticket=ticket,
                workspace=workspace,
                granted_by=request.user,
                expires_at=expires_at,
                status="ACTIVE",
                reason=reason,
            )
        finally:
            _current_audit_context.reset(token)

        serializer = TechnicianAssignmentSerializer(assignment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], description="Revoke diagnostic pass")
    def revoke_diagnostic_pass(self, request, pk=None):
        ticket = self.get_object()
        if not is_admin_or_support_manager(request.user):
            return Response(
                {"error": "Only support managers and administrators can revoke diagnostic passes."},
                status=status.HTTP_403_FORBIDDEN,
            )

        pass_id = request.data.get("pass_id")
        if not pass_id:
            return Response({"error": "pass_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        assignment = TechnicianAssignment.objects.filter(id=pass_id, ticket=ticket).first()
        if not assignment:
            assignment = TechnicianAssignment.objects.filter(id=pass_id).first()
        if not assignment:
            return Response({"error": "Diagnostic pass not found."}, status=status.HTTP_404_NOT_FOUND)

        token = _current_audit_context.set({
            "action_detail": "revoke_diagnostic_pass",
            "actor": request.user,
            "pass_id": str(assignment.id),
            "ticket_id": str(ticket.id),
        })
        try:
            assignment.status = "REVOKED"
            assignment.save()
        finally:
            _current_audit_context.reset(token)

        return Response({"status": "pass_revoked"}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], description="Get support members")
    def get_support_members(self, request):
        support_members = SupportMembership.objects.select_related("user").all()
        data = [
            {
                "id": member.user.id,
                "full_name": member.user.get_full_name() or member.user.username,
                "role": member.role,
            }
            for member in support_members
        ]
        return Response(data)

    @action(detail=False, methods=["get"], description="Get all classification types")
    def get_all_types(self, request):
        return Response(
            {
                "priority_levels": dict(PRIORITY_CHOICES),
                "status_types": dict(STATUS_CHOICES),
                "categories": dict(CATEGORY_CHOICES),
                "infrastructure_categories": dict(INFRASTRUCTURE_CATEGORY_CHOICES),
                "machine_types": dict(MACHINE_TYPE_CHOICES),
                "electric_machine_subtypes": dict(ELECTRIC_MACHINE_CHOICES),
                "mechanical_machine_subtypes": dict(MECHANICAL_MACHINE_CHOICES),
                "support_membership_roles": dict(SUPPORT_MEMBERSHIP_ROLE_CHOICES),
            }
        )


@extend_schema_view(
    list=extend_schema(description="Comment List"),
    create=extend_schema(description="Comment Create"),
    retrieve=extend_schema(description="Comment Retrieve"),
    update=extend_schema(description="Comment Update"),
    partial_update=extend_schema(description="Comment Partial Update"),
    destroy=extend_schema(description="Comment Destroy"),
)
class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated, HasContextualPermission]
    scope = "comment"

    def get_queryset(self):
        user = self.request.user
        if not user or not user.is_authenticated:
            return Comment.objects.none()
        if user.is_superuser or is_global_support_manager(user):
            return Comment.objects.all()
        tenant = getattr(self.request, "tenant", getattr(user, "tenant", None))
        return Comment.objects.filter(
            models.Q(ticket__tenant=tenant) | models.Q(ticket__assigned_to=user)
        )

    def perform_create(self, serializer):
        ticket = serializer.validated_data.get("ticket")
        user = self.request.user
        if ticket and not user.is_superuser and not is_global_support_manager(user):
            tenant = getattr(self.request, "tenant", getattr(user, "tenant", None))
            if ticket.tenant != tenant and ticket.assigned_to != user:
                raise PermissionDenied("Cannot post comments on tickets outside your tenant unless assigned to it.")

        comment = serializer.save()
        ticket = comment.ticket

        commenter = self.request.user or None

        if not commenter or not is_support_member(commenter):
            ticket.is_read = False

        ticket.save()

        if comment.response:
            # Comment from technician/staff
            if ticket.user_id:
                try:
                    ticket_user = User.objects.get(id=ticket.user_id)
                    ticket_user_name = (
                        ticket_user.get_full_name() or ticket_user.username
                    )
                    ticket_user_email = ticket_user.email
                except User.DoesNotExist:
                    ticket_user_name = ticket.guest_name
                    ticket_user_email = ticket.guest_email
            else:
                ticket_user_name = ticket.guest_name
                ticket_user_email = ticket.guest_email

            token = generate_token(
                scope="ticket_access",
                expires_minutes=60 * 24 * 3,
                ticket_id=str(ticket.id),
            )  # 3 days validity

            send_ticket_updated_notification_email(
                name=ticket_user_name,
                email=ticket_user_email,
                ticket=ticket,
                comment=comment,
                token=token,
            )
        else:
            # Comment from user/guest
            assigned_staff = ticket.assigned_to
            if assigned_staff:
                send_ticket_updated_notification_email_to_staff(
                    staff_email=assigned_staff.email,
                    ticket=ticket,
                    comment=comment,
                )

        return comment


@extend_schema_view(
    list=extend_schema(description="Attachment List"),
    create=extend_schema(description="Attachment Create"),
    retrieve=extend_schema(description="Attachment Retrieve"),
    update=extend_schema(description="Attachment Update"),
    partial_update=extend_schema(description="Attachment Partial Update"),
    destroy=extend_schema(description="Attachment Destroy"),
)
class AttachmentViewSet(viewsets.ModelViewSet):
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer
    permission_classes = [IsAuthenticated, HasContextualPermission]
    scope = "attachment"

    def get_queryset(self):
        user = self.request.user
        if not user or not user.is_authenticated:
            return Attachment.objects.none()
        if user.is_superuser or is_global_support_manager(user):
            return Attachment.objects.all()
        tenant = getattr(self.request, "tenant", getattr(user, "tenant", None))
        return Attachment.objects.filter(
            models.Q(ticket__tenant=tenant) | models.Q(ticket__assigned_to=user)
        )

    def perform_create(self, serializer):
        ticket = serializer.validated_data.get("ticket")
        user = self.request.user
        if ticket and not user.is_superuser and not is_global_support_manager(user):
            tenant = getattr(self.request, "tenant", getattr(user, "tenant", None))
            if ticket.tenant != tenant and ticket.assigned_to != user:
                raise PermissionDenied("Cannot add attachments to tickets outside your tenant unless assigned to it.")
        return serializer.save()


@extend_schema_view(
    list=extend_schema(description="Comment Attachment List"),
    create=extend_schema(description="Comment Attachment Create"),
    retrieve=extend_schema(description="Comment Attachment Retrieve"),
    update=extend_schema(description="Comment Attachment Update"),
    partial_update=extend_schema(description="Comment Attachment Partial Update"),
    destroy=extend_schema(description="Comment Attachment Destroy"),
)
class CommentAttachmentViewSet(viewsets.ModelViewSet):
    queryset = CommentAttachment.objects.all()
    serializer_class = CommentAttachmentSerializer
    permission_classes = [IsAuthenticated, HasContextualPermission]
    scope = "commentattachment"

    def get_queryset(self):
        user = self.request.user
        if not user or not user.is_authenticated:
            return CommentAttachment.objects.none()
        if user.is_superuser or is_global_support_manager(user):
            return CommentAttachment.objects.all()
        tenant = getattr(self.request, "tenant", getattr(user, "tenant", None))
        return CommentAttachment.objects.filter(
            models.Q(comment__ticket__tenant=tenant) | models.Q(comment__ticket__assigned_to=user)
        )

    def perform_create(self, serializer):
        comment = serializer.validated_data.get("comment")
        user = self.request.user
        if comment and not user.is_superuser and not is_global_support_manager(user):
            tenant = getattr(self.request, "tenant", getattr(user, "tenant", None))
            ticket = getattr(comment, "ticket", None)
            if ticket and ticket.tenant != tenant and ticket.assigned_to != user:
                raise PermissionDenied("Cannot add attachments to comments outside your tenant unless assigned to it.")
        return serializer.save()


@extend_schema_view(
    list=extend_schema(description="Support Membership List"),
    create=extend_schema(description="Support Membership Create"),
    retrieve=extend_schema(description="Support Membership Retrieve"),
    update=extend_schema(description="Support Membership Update"),
    partial_update=extend_schema(description="Support Membership Partial Update"),
    destroy=extend_schema(description="Support Membership Destroy"),
)
class SupportMembershipViewSet(viewsets.ModelViewSet):
    queryset = SupportMembership.objects.all()
    serializer_class = SupportMembershipSerializer
    permission_classes = [IsAuthenticated, HasContextualPermission]
    scope = "supportmembership"

    def get_queryset(self):
        user = self.request.user
        if not user or not user.is_authenticated:
            return SupportMembership.objects.none()
        if user.is_superuser or is_global_support_manager(user):
            return SupportMembership.objects.all()
        tenant = getattr(self.request, "tenant", getattr(user, "tenant", None))
        return SupportMembership.objects.filter(
            models.Q(tenant=tenant) | models.Q(tenant__isnull=True)
        )

    def perform_create(self, serializer):
        instance = serializer.save()
        user = instance.user
        support_managers = SupportMembership.objects.filter(role="support_manager")
        support_managers_count = support_managers.count()
        if support_managers_count > 1:
            for support_manager in support_managers:
                support_manager_can_view_all_support_members(
                    support_manager=support_manager, user=user
                )
        elif support_managers_count == 1:
            support_manager = support_managers.first()
            support_manager_can_view_all_support_members(
                support_manager=support_manager, user=user
            )
        return instance


@extend_schema_view(
    list=extend_schema(description="Technician Assignment List"),
    create=extend_schema(description="Technician Assignment Create"),
    retrieve=extend_schema(description="Technician Assignment Retrieve"),
    update=extend_schema(description="Technician Assignment Update"),
    partial_update=extend_schema(description="Technician Assignment Partial Update"),
    destroy=extend_schema(description="Technician Assignment Destroy"),
)
class TechnicianAssignmentViewSet(viewsets.ModelViewSet):
    queryset = TechnicianAssignment.objects.all()
    serializer_class = TechnicianAssignmentSerializer
    permission_classes = [IsAuthenticated, HasContextualPermission]
    scope = "technicianassignment"

    def get_queryset(self):
        user = self.request.user
        if not user or not user.is_authenticated:
            return TechnicianAssignment.objects.none()
        if user.is_superuser or is_global_support_manager(user):
            return TechnicianAssignment.objects.all()
        tenant = getattr(self.request, "tenant", getattr(user, "tenant", None))
        return TechnicianAssignment.objects.filter(
            models.Q(technician=user) | models.Q(workspace__tenant=tenant)
        )
