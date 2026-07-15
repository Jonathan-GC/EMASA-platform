import requests
from cryptography.fernet import Fernet
from django.conf import settings
from loguru import logger


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


def debug_update_deveui_mapping(dev_eui: str):
    hermes_url = getattr(settings, "HERMES_API_URL", "")
    if not hermes_url:
        logger.error("HERMES_API_URL is not configured")
        return None

    url = f"{hermes_url}/internal/mappings/device-user"
    headers = {"X-API-Key": getattr(settings, "SERVICE_API_KEY", "")}

    try:
        response = requests.post(url, headers=headers, params={"dev_eui": dev_eui}, timeout=10)
        return response.json()
    except Exception as e:
        logger.exception(f"Failed to update device-user mapping for {dev_eui}: {e}")
        return None
