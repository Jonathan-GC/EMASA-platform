from django.db import models
from users.models import User
import uuid
from organizations.hasher import generate_id

SUPPORT_MEMBERSHIP_ROLE_CHOICES = [
    ("support_agent", "Support Agent"),
    ("support_manager", "Support Manager"),
    ("technician", "Technician"),
    ("other", "Other"),
]

PRIORITY_CHOICES = [
    ("low", "Low"),
    ("medium", "Medium"),
    ("high", "High"),
    ("urgent", "Urgent"),
]

STATUS_CHOICES = [
    ("open", "Open"),
    ("in_progress", "In Progress"),
    ("resolved", "Resolved"),
    ("closed", "Closed"),
]

CATEGORY_CHOICES = [
    ("general", "General"),
    ("account", "Account"),
    ("technical", "Technical"),
    ("infrastructure", "Infrastructure"),
    ("billing", "Billing"),
    ("feedback", "Feedback"),
    ("other", "Other"),
]

INFRASTRUCTURE_CATEGORY_CHOICES = [
    ("devices", "Devices"),
    ("gateways", "Gateways"),
    ("machines", "Machines"),
    ("applications", "Applications"),
    ("measurements", "Measurements"),
    ("other", "Other"),
]

MACHINE_TYPE_CHOICES = [
    ("electric", "Motor Eléctrico"),
    ("mechanical", "Motor Mecánico"),
]

ELECTRIC_MACHINE_CHOICES = [
    ("motor", "Motor"),
    ("motobomba", "Motobomba"),
    ("motoreductor", "Motoreductor"),
    ("ventilador", "Ventilador"),
    ("compresor", "Compresor"),
    ("vibrador", "Vibrador"),
    ("muela", "Muela"),
    ("torre_grua", "Torre Grúa"),
]

MECHANICAL_MACHINE_CHOICES = [
    ("motor_diesel", "Motor Diésel"),
    ("motor_gasolina", "Motor Gasolina"),
    ("motobomba", "Motobomba"),
    ("mixer", "Mixer"),
    ("barco", "Barco"),
    ("mula", "Mula"),
    ("damper", "Dámper"),
    ("planta_electrica", "Planta Eléctrica"),
    ("compresor", "Compresor"),
    ("vibrador", "Vibrador"),
    ("compactador", "Compactador"),
    ("retroexcavadora", "Retroexcavadora"),
    ("niveladora", "Niveladora"),
    ("combinada", "Combinada"),
    ("tractor", "Tractor"),
]


class SupportMembership(models.Model):
    id = models.CharField(
        max_length=16, primary_key=True, default=generate_id, editable=False
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(
        max_length=20, choices=SUPPORT_MEMBERSHIP_ROLE_CHOICES, default="other"
    )
    tenant = models.ForeignKey(
        "organizations.Tenant",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="support_memberships",
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username


# Create your models here.
class Ticket(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField()

    # Classification fields
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Open")
    priority = models.CharField(
        max_length=20, choices=PRIORITY_CHOICES, default="Medium"
    )
    category = models.CharField(
        max_length=50, choices=CATEGORY_CHOICES, default="General"
    )
    infrastructure_category = models.CharField(
        max_length=50,
        choices=INFRASTRUCTURE_CATEGORY_CHOICES,
        default="Other",
    )
    machine_type = models.CharField(
        max_length=20, choices=MACHINE_TYPE_CHOICES, null=True, blank=True
    )
    electric_machine_subtype = models.CharField(
        max_length=50,
        choices=ELECTRIC_MACHINE_CHOICES,
        null=True,
        blank=True,
    )
    mechanical_machine_subtype = models.CharField(
        max_length=50,
        choices=MECHANICAL_MACHINE_CHOICES,
        null=True,
        blank=True,
    )

    tenant = models.ForeignKey(
        "organizations.Tenant",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="tickets",
    )
    workspace = models.ForeignKey(
        "organizations.Workspace",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tickets",
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    guest_name = models.CharField(max_length=100, null=True, blank=True)
    guest_email = models.EmailField(null=True, blank=True)
    organization = models.CharField(max_length=200, null=True, blank=True)

    assigned_to = models.ForeignKey(
        User,
        related_name="assigned_tickets",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    is_read = models.BooleanField(default=False)

    @property
    def technician_assignments(self):
        return self.diagnostic_passes

    def clean(self):
        from django.core.exceptions import ValidationError

        if not self.user and (not self.guest_name or not self.guest_email):
            raise ValidationError("Guest tickets must have a name and email address.")
        if self.workspace and self.tenant and self.workspace.tenant_id != self.tenant_id:
            raise ValidationError("The selected workspace does not belong to the ticket's tenant.")

    def __str__(self):
        return self.title


ASSIGNMENT_STATUS_CHOICES = [
    ("ACTIVE", "Active"),
    ("EXPIRED", "Expired"),
    ("REVOKED", "Revoked"),
]


class TechnicianAssignment(models.Model):
    id = models.CharField(
        max_length=16, primary_key=True, default=generate_id, editable=False
    )
    technician = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="technician_passes"
    )
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="diagnostic_passes",
    )
    workspace = models.ForeignKey(
        "organizations.Workspace",
        on_delete=models.CASCADE,
        related_name="diagnostic_passes",
    )
    granted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="granted_diagnostic_passes",
    )
    granted_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    status = models.CharField(
        max_length=20, choices=ASSIGNMENT_STATUS_CHOICES, default="ACTIVE"
    )
    reason = models.TextField(blank=True, default="")

    def is_valid(self):
        from django.utils import timezone
        return (self.status or "").upper() == "ACTIVE" and timezone.now() < self.expires_at

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.pk:
            orig = TechnicianAssignment.objects.filter(pk=self.pk).values("status").first()
            if orig and orig["status"].upper() in ["EXPIRED", "REVOKED"] and (self.status or "").upper() == "ACTIVE":
                raise ValidationError("Cannot reactivate an expired or revoked diagnostic pass.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Pass {self.id} for {self.technician.username} on {self.workspace.name} ({self.status})"


class Comment(models.Model):
    id = models.CharField(
        max_length=16, primary_key=True, default=generate_id, editable=False
    )
    ticket = models.ForeignKey(
        Ticket, related_name="comments", on_delete=models.CASCADE
    )
    response = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    guest_name = models.CharField(max_length=100, null=True, blank=True)
    guest_email = models.EmailField(null=True, blank=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.ticket.title} - Comment"


class Attachment(models.Model):
    id = models.CharField(
        max_length=16, primary_key=True, default=generate_id, editable=False
    )
    ticket = models.ForeignKey(
        Ticket, related_name="attachments", on_delete=models.CASCADE
    )
    file = models.FileField(upload_to="support/attachments/ticket/%Y/%m/%d/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.file.name


class CommentAttachment(models.Model):
    id = models.CharField(
        max_length=16, primary_key=True, default=generate_id, editable=False
    )
    comment = models.ForeignKey(
        Comment, related_name="attachments", on_delete=models.CASCADE
    )
    file = models.FileField(upload_to="support/attachments/comment/%Y/%m/%d/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.file.name


from auditlog.registry import auditlog

auditlog.register(Ticket, exclude_fields=["updated_at", "is_read"])
auditlog.register(Comment)
auditlog.register(Attachment)
auditlog.register(CommentAttachment)
auditlog.register(TechnicianAssignment)
