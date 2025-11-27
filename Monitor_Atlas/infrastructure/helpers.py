from cryptography.fernet import Fernet
from django.conf import settings


def encrypt_dev_eui(dev_eui: str) -> str:
    try:
        secret = settings.WS_SECRET.encode("utf-8")
    except Exception as e:
        raise ValueError(
            "WS_SECRET must be set in settings and be a valid base64-encoded 32-byte key."
        ) from e
    try:
        fernet = Fernet(secret)
    except Exception as e:
        raise ValueError("WS_SECRET must be a valid base64-encoded 32-byte key.") from e

    encrypted_dev_eui = fernet.encrypt(dev_eui.encode("utf-8"))

    return encrypted_dev_eui.decode("utf-8")
