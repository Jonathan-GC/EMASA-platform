import json
import requests

from urllib.parse import urlencode

from django.conf import settings


MAILGUN_API_KEY = settings.MAILGUN_API_KEY
MAILGUN_DOMAIN = settings.MAILGUN_DOMAIN
MAILGUN_FROM = settings.MAILGUN_FROM
APP_URL = settings.APP_URL

MTR_LOGO_URL = settings.MTR_LOGO_URL

MAILGUN_BASE_URL = f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages"


def send_email(
    to: str,
    subject: str,
    text: str,
    html: str = None,
    template: str = None,
    vars: dict = None,
):
    """Send an email using Mailgun API.
    param to: Recipient email address
    param subject: Email subject
    param text: Plain text email body
    param html: Optional HTML email body
    """
    if not MAILGUN_API_KEY or not MAILGUN_DOMAIN:
        raise ValueError("Mailgun API key and domain must be set in settings.")

    data = {
        "from": MAILGUN_FROM,
        "to": to,
        "subject": subject,
        "text": text,
    }
    if html:
        data["html"] = html
    if template:
        data["template"] = template
    if vars:
        data["t:variables"] = json.dumps(vars)

    response = requests.post(
        MAILGUN_BASE_URL,
        auth=("api", MAILGUN_API_KEY),
        data=data,
        timeout=10,
    )

    print(response.status_code, response.text)

    try:
        response.raise_for_status()
    except Exception:
        raise Exception(f"Failed to send email: {response.text}")

    return response.json()


def send_verification_email(user, token: str):
    """Send a verification email to the user.
    param user: User object with 'email' and 'name' attributes
    param token: Verification token string
    """
    to = user.email
    subject = "Verify your email"
    verify_link = f"{APP_URL}/verify-email?{urlencode({'token': token})}"
    text = f"Please verify your email by clicking the following link: {verify_link}"
    vars = {
        "logo_url": MTR_LOGO_URL,
        "urltoken": verify_link,
        "name": user.name,
        "username": user.username,
    }
    return send_email(
        to, subject, text=text, template="account.verification", vars=vars
    )


def send_password_reset_email(user, token: str):
    """Send a password reset email to the user using a Mailgun template.

    param user: User object with 'email', 'name', and 'id' attributes
    param token: Password reset token string
    """
    to = user.email
    subject = "Reset your password"
    reset_link = f"{APP_URL}/reset-password?{urlencode({'token': token})}"
    text = f"Please reset your password by clicking the following link: {reset_link}"
    vars = {"logo_url": MTR_LOGO_URL, "urltoken": reset_link, "name": user.name}

    return send_email(to, subject, text=text, template="password.recovery", vars=vars)


def send_ticket_created_notification_email(name, email, ticket, token: str):
    """Send a ticket notification email to the user.

    param user: User object with 'email' and 'name' attributes
    param ticket: Ticket object with 'id', 'title', and 'status' attributes
    param comment: Optional Comment object with 'content' attribute
    """
    to = email
    subject = f"New Ticket #{ticket.id}: {ticket.title}"
    ticket_link = f"{APP_URL}/tickets?{urlencode({'token': token})}"
    text = (
        f"You have created a new ticket '{ticket.title}'. View it here: {ticket_link}"
    )
    vars = {
        "logo_url": MTR_LOGO_URL,
        "ticket_id": str(ticket.id),
        "ticket_title": ticket.title,
        "ticket_status": ticket.status,
        "ticket_link": ticket_link,
        "name": name,
    }

    return send_email(to, subject, text=text, template="ticket.create", vars=vars)


def send_ticket_updated_notification_email(name, email, ticket, comment, token: str):
    """Send a ticket notification email to the user.

    param user: User object with 'email' and 'name' attributes
    param ticket: Ticket object with 'id', 'title', and 'status' attributes
    param comment: Optional Comment object with 'content' attribute
    """
    to = email
    subject = f"Ticket #{ticket.id} Updated: {ticket.title}"
    ticket_link = f"{APP_URL}/tickets?{urlencode({'token': token})}"
    text = f"Your ticket '{ticket.title}' has been updated. View it here: {ticket_link}"
    vars = {
        "logo_url": MTR_LOGO_URL,
        "ticket_id": str(ticket.id),
        "ticket_title": ticket.title,
        "ticket_status": ticket.status,
        "ticket_link": ticket_link,
        "comment_content": comment.content if comment else "",
        "name": name,
    }

    return send_email(to, subject, text=text, template="ticket.notification", vars=vars)


def send_new_ticket_notification_email_to_staff(staff_email, ticket, comment):
    """Send a new ticket notification email to support staff.

    param staff_email: Support staff email address
    param ticket: Ticket object with 'id', 'title', and 'status' attributes
    param comment: Optional Comment object with 'content' attribute
    """
    to = staff_email
    subject = f"New Ticket #{ticket.id}: {ticket.title}"
    text = (
        f"A new ticket '{ticket.title}' has been created with status '{ticket.status}'."
    )
    ticket_link = f"{APP_URL}"
    vars = {
        "logo_url": MTR_LOGO_URL,
        "ticket_id": str(ticket.id),
        "ticket_title": ticket.title,
        "ticket_status": ticket.status,
        "comment_content": comment.content if comment else "",
        "ticket_link": ticket_link,
    }

    return send_email(to, subject, text=text, template="ticket.staff", vars=vars)


def send_ticket_updated_notification_email_to_staff(staff_email, ticket, comment):
    """Send a ticket updated notification email to support staff.

    param staff_email: Support staff email address
    param ticket: Ticket object with 'id', 'title', and 'status' attributes
    param comment: Optional Comment object with 'content' attribute
    """
    to = staff_email
    subject = f"Ticket #{ticket.id} Updated: {ticket.title}"
    text = f"The ticket '{ticket.title}' has been updated to status '{ticket.status}'."
    ticket_link = f"{APP_URL}"
    vars = {
        "logo_url": MTR_LOGO_URL,
        "ticket_id": str(ticket.id),
        "ticket_title": ticket.title,
        "ticket_status": ticket.status,
        "comment_content": comment.content if comment else "",
        "ticket_link": ticket_link,
    }

    return send_email(to, subject, text=text, template="ticket.staff", vars=vars)
