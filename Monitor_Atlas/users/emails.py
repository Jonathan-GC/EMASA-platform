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


def send_otp_email(user, code: str):
    """Send an OTP code to the user for email login.

    param user: User object with 'email' and 'name' attributes
    param code: 6-digit OTP code string
    """
    to = user.email
    subject = f"Tu código de inicio de sesión: {code}"
    text = (
        f"Hola {user.name or user.username},\n\n"
        f"Tu código de verificación para iniciar sesión en Monitor Atlas es: {code}\n\n"
        f"Este código es válido por 5 minutos. No lo compartas con nadie."
    )
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px;">
        <h2 style="color: #1a73e8;">Código de Verificación</h2>
        <p>Hola <strong>{user.name or user.username}</strong>,</p>
        <p>Tu código de verificación para iniciar sesión en Monitor Atlas es:</p>
        <div style="background-color: #f1f3f4; padding: 15px; border-radius: 6px; text-align: center; font-size: 32px; font-weight: bold; letter-spacing: 5px; color: #202124; margin: 20px 0;">
            {code}
        </div>
        <p>Este código expira en <strong>5 minutos</strong>. Si no solicitaste este código, puedes ignorar este mensaje.</p>
    </div>
    """
    vars = {
        "logo_url": MTR_LOGO_URL,
        "otp_code": code,
        "name": user.name or user.username,
    }

    try:
        return send_email(
            to, subject, text=text, html=html, template="account.otp", vars=vars
        )
    except Exception:
        return send_email(to, subject, text=text, html=html)

