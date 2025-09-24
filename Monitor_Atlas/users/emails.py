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
    html = f"""
    <html>
        <body>
            <h1>Verify your email</h1>
            <p>Hi {user.name},</p>
            <p>Please verify your email by clicking the following link:</p>
            <a href="{verify_link}">Verify Email</a>
        </body>
    </html>
    """
    return send_email(to, subject, text, html)


def send_password_reset_email(user, token: str):
    """Send a password reset email to the user.

    param user: User object with 'email', 'name', and 'id' attributes
    param token: Password reset token string
    """
    to = user.email
    subject = "Reset your password"
    reset_link = (
        f"{APP_URL}/reset-password?{urlencode({'token': token, 'uid': user.id})}"
    )
    text = f"Please reset your password by clicking the following link: {reset_link}"
    html = f"""
    <html>
        <body>
            <h1>Reset your password</h1>
            <p>Hi {user.name},</p>
            <p>Please reset your password by clicking the following link:</p>
            <a href="{reset_link}">Reset Password</a>
        </body>
    </html>
    """
    return send_email(to, subject, text, html)


def send_password_reset_email_with_template(user, token: str):
    """Send a password reset email to the user using a Mailgun template.

    param user: User object with 'email', 'name', and 'id' attributes
    param token: Password reset token string
    """
    to = user.email
    subject = "Reset your password"
    reset_link = (
        f"{APP_URL}/reset-password?{urlencode({'token': token, 'uid': user.id})}"
    )
    text = f"Please reset your password by clicking the following link: {reset_link}"
    vars = {"logo_url": MTR_LOGO_URL, "urltoken": reset_link, "nombre": user.name}

    return send_email(to, subject, text=text, template="password.recovery", vars=vars)
