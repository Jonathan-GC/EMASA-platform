import os
import requests

from urllib.parse import urlencode

from django.conf import settings


MAILGUN_API_KEY = settings.MAILGUN_API_KEY
MAILGUN_DOMAIN = settings.MAILGUN_DOMAIN
MAILGUN_FROM = settings.MAILGUN_FROM
APP_URL = settings.APP_URL

MAILGUN_BASE_URL = f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages"


def send_email(to: str, subject: str, text: str, html: str = None):
    if not MAILGUN_API_KEY or not MAILGUN_DOMAIN:
        raise ValueError("Mailgun API key and domain must be set in settings.")

    # Do NOT set Content-Type here; requests will add the correct multipart boundary.
    # headers = {"Content-Type": "multipart/form-data"}

    data = {
        "from": MAILGUN_FROM,
        "to": to,
        "subject": subject,
        "text": text,
    }
    if html:
        data["html"] = html

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
