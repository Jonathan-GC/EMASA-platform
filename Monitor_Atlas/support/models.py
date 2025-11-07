from django.db import models
from users.models import User
import requests
from django.conf import settings
from loguru import logger

HERMES_API_URL = getattr(settings, "HERMES_API_URL", "http://localhost:5000")

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

NOTIFICATION_TYPE_CHOICES = [
    ("info", "Info"),
    ("warning", "Warning"),
    ("error", "Error"),
    ("success", "Success"),
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
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(
        max_length=20, choices=SUPPORT_MEMBERSHIP_ROLE_CHOICES, default="other"
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.role}"


# Create your models here.
class Ticket(models.Model):
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

    def clean(self):
        from django.core.exceptions import ValidationError

        if not self.user and (not self.guest_name or not self.guest_email):
            raise ValidationError("Guest tickets must have a name and email address.")

    def __str__(self):
        user_repr = self.user.username if self.user else self.guest_email
        return f"{self.title} - {self.status} - {self.priority} - {user_repr}"


class Comment(models.Model):
    ticket = models.ForeignKey(
        Ticket, related_name="comments", on_delete=models.CASCADE
    )
    response = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.user.username} on {self.ticket.title}"


class Attachment(models.Model):
    ticket = models.ForeignKey(
        Ticket, related_name="attachments", on_delete=models.CASCADE
    )
    file = models.FileField(upload_to="support/attachments/ticket/%Y/%m/%d/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Attachment for {self.ticket.title}"


class CommentAttachment(models.Model):
    comment = models.ForeignKey(
        Comment, related_name="attachments", on_delete=models.CASCADE
    )
    file = models.FileField(upload_to="support/attachments/comment/%Y/%m/%d/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Attachment for comment {self.comment.id} on ticket {self.comment.ticket.title}"


class Notification(models.Model):
    title = models.CharField(max_length=200, default="Notification")
    message = models.TextField()
    type = models.CharField(
        max_length=20, choices=NOTIFICATION_TYPE_CHOICES, default="info"
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def mark_as_read(self):
        self.is_read = True
        self.save()

    def notify_ws(self):
        logger.debug("Sending WebSocket notification via Hermes")

        url = f"{HERMES_API_URL}/notify"

        headers = {"X-API-Key": settings.SERVICE_API_KEY}

        data = {
            "user_id": self.user.id,
            "title": self.title,
            "message": self.message,
            "type": self.type,
        }

        try:
            logger.debug(f"Notification data: {data} \n to {url}")
            response = requests.post(url, data=data, headers=headers, timeout=5)
            response.raise_for_status()
            logger.debug(f"WebSocket notification sent: {response.status_code}")
        except requests.RequestException as e:
            logger.error(f"Failed to send notification via WebSocket: {e}")

    def __str__(self):
        return f"Notification for {self.user.username} - {self.type}"
