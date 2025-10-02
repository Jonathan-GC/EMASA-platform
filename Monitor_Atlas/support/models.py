from django.db import models
from users.models import User

PRIORITY_CHOICES = [
    ("Low", "Low"),
    ("Medium", "Medium"),
    ("High", "High"),
    ("Urgent", "Urgent"),
]

STATUS_CHOICES = [
    ("Open", "Open"),
    ("In Progress", "In Progress"),
    ("Resolved", "Resolved"),
    ("Closed", "Closed"),
]

NOTIFICATION_TYPE_CHOICES = [
    ("info", "Info"),
    ("warning", "Warning"),
    ("error", "Error"),
]


# Create your models here.
class Ticket(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Open")
    priority = models.CharField(
        max_length=20, choices=PRIORITY_CHOICES, default="Medium"
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    guest_name = models.CharField(max_length=100, null=True, blank=True)
    guest_email = models.EmailField(null=True, blank=True)

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

    def __str__(self):
        return f"Notification for {self.user.username} - {self.type}"
