import os
import time
from datetime import datetime, timezone
import requests
import boto3
import botocore
from botocore.config import Config
from django.conf import settings
from django.db import connection
from loguru import logger


def check_database_health() -> dict:
    """Check the default PostgreSQL database connection and measure latency."""
    start = time.perf_counter()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
            cursor.fetchone()
        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        db_conf = settings.DATABASES.get("default", {})
        engine = db_conf.get("ENGINE", "").split(".")[-1]
        return {
            "status": "healthy",
            "latency_ms": latency_ms,
            "engine": engine,
            "database": db_conf.get("NAME"),
            "host": db_conf.get("HOST"),
        }
    except Exception as e:
        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.exception(f"Database healthcheck failed: {e}")
        return {
            "status": "unhealthy",
            "latency_ms": latency_ms,
            "error": str(e),
        }


def check_r2_storage_health() -> dict:
    """
    Check Cloudflare R2 / S3 storage health if USE_R2 is enabled.
    Falls back to checking local media storage if disabled.
    """
    use_r2 = getattr(settings, "USE_R2", False)
    if not use_r2:
        media_root = getattr(settings, "MEDIA_ROOT", None)
        writable = False
        if media_root:
            try:
                os.makedirs(media_root, exist_ok=True)
                writable = os.access(media_root, os.W_OK)
            except Exception:
                writable = False
        return {
            "enabled": False,
            "backend": "filesystem",
            "status": "healthy" if writable else "degraded",
            "media_root_writable": writable,
        }

    bucket_name = getattr(settings, "R2_BUCKET_NAME", None)
    endpoint_url = getattr(settings, "R2_ENDPOINT_URL", None)
    access_key = getattr(settings, "R2_ACCESS_KEY_ID", None)
    secret_key = getattr(settings, "R2_SECRET_ACCESS_KEY", None)
    custom_domain = getattr(settings, "R2_CUSTOM_DOMAIN", None)
    region_name = getattr(settings, "R2_REGION_NAME", "auto")

    if not all([bucket_name, endpoint_url, access_key, secret_key]):
        return {
            "enabled": True,
            "backend": "s3_r2",
            "status": "unhealthy",
            "bucket": bucket_name,
            "endpoint_url": endpoint_url,
            "error": "R2 is enabled but credentials or bucket settings are incomplete",
        }

    start = time.perf_counter()
    try:
        s3_client = boto3.client(
            "s3",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            endpoint_url=endpoint_url,
            region_name=region_name,
            config=Config(
                signature_version="s3v4",
                connect_timeout=5,
                read_timeout=5,
                retries={"max_attempts": 1},
            ),
        )
        s3_client.head_bucket(Bucket=bucket_name)
        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        return {
            "enabled": True,
            "backend": "s3_r2",
            "status": "healthy",
            "bucket": bucket_name,
            "endpoint_url": endpoint_url,
            "custom_domain": custom_domain,
            "latency_ms": latency_ms,
        }
    except botocore.exceptions.ClientError as e:
        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        error_code = e.response.get("Error", {}).get("Code", "ClientError")
        logger.warning(f"R2 healthcheck ClientError: {e}")
        return {
            "enabled": True,
            "backend": "s3_r2",
            "status": "unhealthy",
            "bucket": bucket_name,
            "endpoint_url": endpoint_url,
            "latency_ms": latency_ms,
            "error": f"S3 ClientError ({error_code}): {str(e)}",
        }
    except Exception as e:
        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.warning(f"R2 healthcheck exception: {e}")
        return {
            "enabled": True,
            "backend": "s3_r2",
            "status": "unhealthy",
            "bucket": bucket_name,
            "endpoint_url": endpoint_url,
            "latency_ms": latency_ms,
            "error": str(e),
        }


def check_mailgun_health() -> dict:
    """
    Check Mailgun service connectivity using a standard GET request to verify
    the configured domain / credentials.
    """
    api_key = getattr(settings, "MAILGUN_API_KEY", None)
    domain = getattr(settings, "MAILGUN_DOMAIN", None)

    if not api_key or not domain:
        return {
            "configured": False,
            "status": "not_configured",
            "message": "Mailgun credentials not configured in settings",
        }

    start = time.perf_counter()
    try:
        url = f"https://api.mailgun.net/v3/domains/{domain}"
        response = requests.get(
            url,
            auth=("api", api_key),
            timeout=5,
        )
        latency_ms = round((time.perf_counter() - start) * 1000, 2)

        if response.status_code == 200:
            domain_info = {}
            try:
                domain_info = response.json().get("domain", {})
            except Exception:
                pass
            return {
                "configured": True,
                "status": "healthy",
                "domain": domain,
                "domain_state": domain_info.get("state", "active"),
                "http_status": response.status_code,
                "latency_ms": latency_ms,
            }
        elif response.status_code == 401:
            return {
                "configured": True,
                "status": "unhealthy",
                "domain": domain,
                "http_status": response.status_code,
                "latency_ms": latency_ms,
                "error": "Mailgun API key is unauthorized (401)",
            }
        else:
            return {
                "configured": True,
                "status": "degraded",
                "domain": domain,
                "http_status": response.status_code,
                "latency_ms": latency_ms,
                "error": f"Mailgun returned status {response.status_code}",
            }
    except Exception as e:
        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.warning(f"Mailgun healthcheck error: {e}")
        return {
            "configured": True,
            "status": "unhealthy",
            "domain": domain,
            "latency_ms": latency_ms,
            "error": str(e),
        }


def check_chirpstack_health() -> dict:
    """Check ChirpStack REST API reachability if configured."""
    base_url = getattr(settings, "CHIRPSTACK_BASE_URL", None)
    jwt_token = getattr(settings, "CHIRPSTACK_JWT_TOKEN", None)

    if not base_url or not jwt_token:
        return {
            "configured": False,
            "status": "not_configured",
            "message": "ChirpStack credentials not configured",
        }

    start = time.perf_counter()
    try:
        url = f"{base_url.rstrip('/')}/tenants?limit=1"
        headers = {"Authorization": f"Bearer {jwt_token}"}
        response = requests.get(url, headers=headers, timeout=5)
        latency_ms = round((time.perf_counter() - start) * 1000, 2)

        if response.status_code == 200:
            return {
                "configured": True,
                "status": "healthy",
                "base_url": base_url,
                "http_status": response.status_code,
                "latency_ms": latency_ms,
            }
        else:
            return {
                "configured": True,
                "status": "degraded",
                "base_url": base_url,
                "http_status": response.status_code,
                "latency_ms": latency_ms,
                "error": f"ChirpStack API returned status {response.status_code}",
            }
    except Exception as e:
        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.warning(f"ChirpStack healthcheck error: {e}")
        return {
            "configured": True,
            "status": "unhealthy",
            "base_url": base_url,
            "latency_ms": latency_ms,
            "error": str(e),
        }


def check_firebase_health() -> dict:
    """Check Firebase Admin SDK configuration status."""
    creds_path = getattr(settings, "FIREBASE_ADMIN_CREDENTIALS", None)
    if not creds_path:
        return {
            "configured": False,
            "status": "not_configured",
            "message": "FIREBASE_ADMIN_CREDENTIALS is not configured",
        }

    resolved_path = os.path.join(settings.BASE_DIR, creds_path) if not os.path.isabs(creds_path) else creds_path
    exists = os.path.exists(resolved_path)
    return {
        "configured": True,
        "status": "healthy" if exists else "degraded",
        "credentials_path": creds_path,
        "file_exists": exists,
    }


def check_hermes_health() -> dict:
    """
    Check Hermes HTTP API health endpoint and retrieve internal component status.
    """
    hermes_api_url = getattr(settings, "HERMES_API_URL", None)
    hermes_ws_url = getattr(settings, "HERMES_WS_URL", None)
    service_api_key = getattr(settings, "SERVICE_API_KEY", "")

    if not hermes_api_url:
        return {
            "configured": False,
            "status": "not_configured",
            "message": "HERMES_API_URL is not configured in settings",
        }

    start = time.perf_counter()
    try:
        url = f"{hermes_api_url.rstrip('/')}/health"
        headers = {"X-API-Key": service_api_key}
        response = requests.get(url, headers=headers, timeout=5)
        latency_ms = round((time.perf_counter() - start) * 1000, 2)

        if response.status_code == 200:
            data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
            hermes_status = data.get("status", "healthy")
            return {
                "configured": True,
                "status": hermes_status,
                "api_url": hermes_api_url,
                "ws_url": hermes_ws_url,
                "latency_ms": latency_ms,
                "details": data,
            }
        else:
            return {
                "configured": True,
                "status": "degraded",
                "api_url": hermes_api_url,
                "ws_url": hermes_ws_url,
                "http_status": response.status_code,
                "latency_ms": latency_ms,
                "error": f"Hermes returned HTTP {response.status_code}",
            }
    except Exception as e:
        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.warning(f"Hermes healthcheck connection failed: {e}")
        return {
            "configured": True,
            "status": "unreachable",
            "api_url": hermes_api_url,
            "ws_url": hermes_ws_url,
            "latency_ms": latency_ms,
            "error": str(e),
        }


def get_atlas_services_health() -> dict:
    """Collect health status across all Atlas internal and connected services."""
    db_health = check_database_health()
    storage_health = check_r2_storage_health()
    mailgun_health = check_mailgun_health()
    chirpstack_health = check_chirpstack_health()
    firebase_health = check_firebase_health()

    # Determine Atlas internal status
    if db_health.get("status") == "healthy":
        if any(h.get("status") in ("unhealthy", "degraded") for h in [storage_health, mailgun_health, chirpstack_health] if h.get("status") != "not_configured"):
            atlas_status = "degraded"
        else:
            atlas_status = "healthy"
    else:
        atlas_status = "unhealthy"

    return {
        "status": atlas_status,
        "database": db_health,
        "storage": storage_health,
        "email": mailgun_health,
        "chirpstack": chirpstack_health,
        "firebase": firebase_health,
    }


def get_system_health_report() -> dict:
    """Generate a complete platform health report encompassing Atlas and Hermes."""
    atlas_health = get_atlas_services_health()
    hermes_health = check_hermes_health()

    atlas_status = atlas_health.get("status")
    hermes_status = hermes_health.get("status")

    if atlas_status == "healthy" and hermes_status in ("healthy", "not_configured"):
        overall_status = "healthy"
    elif atlas_status == "unhealthy" or hermes_status in ("unhealthy", "unreachable"):
        overall_status = "unhealthy" if atlas_status == "unhealthy" else "degraded"
    else:
        overall_status = "degraded"

    version = getattr(settings, "SPECTACULAR_SETTINGS", {}).get("VERSION", "1.2.0")

    return {
        "status": overall_status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": version,
        "services": {
            "atlas": atlas_health,
            "hermes": hermes_health,
        },
    }
