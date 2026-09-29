import hashlib
import re
from datetime import timedelta
from typing import Any, Dict, Optional, Tuple
from django.db import models
from django.utils import timezone

from users.models import UserSession


def parse_device_name(user_agent: str) -> str:
    """
    Parses a user agent string into a human-readable device name.
    e.g. 'Chrome on Linux', 'Safari on iOS', 'Firefox on Windows'.
    """
    if not user_agent:
        return "Dispositivo desconocido"

    ua = user_agent.lower()

    # Browser
    browser = "Navegador"
    if "edg/" in ua or "edge/" in ua:
        browser = "Edge"
    elif "chrome/" in ua and "chromium" not in ua and "edg" not in ua:
        browser = "Chrome"
    elif "firefox/" in ua:
        browser = "Firefox"
    elif "safari/" in ua and "chrome" not in ua:
        browser = "Safari"
    elif "opera/" in ua or "opr/" in ua:
        browser = "Opera"

    # OS / Platform
    os_name = "desconocido"
    if "windows" in ua:
        os_name = "Windows"
    elif "macintosh" in ua or "mac os" in ua:
        os_name = "macOS"
    elif "iphone" in ua:
        os_name = "iPhone"
    elif "ipad" in ua:
        os_name = "iPad"
    elif "android" in ua:
        os_name = "Android"
    elif "linux" in ua:
        os_name = "Linux"

    return f"{browser} en {os_name}"


def extract_os_family(user_agent: str) -> Optional[str]:
    """
    Extracts high-level operating system family for platform fingerprinting.
    """
    if not user_agent:
        return None
    ua = user_agent.lower()
    if "windows" in ua:
        return "windows"
    if "iphone" in ua or "ipad" in ua or "ios" in ua:
        return "ios"
    if "macintosh" in ua or "mac os" in ua:
        return "macos"
    if "android" in ua:
        return "android"
    if "linux" in ua:
        return "linux"
    return None


def get_client_ip(request: Any) -> Optional[str]:
    """
    Extracts the client IP from request headers or REMOTE_ADDR.
    """
    if not request:
        return None
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


class AdaptiveTrustEngine:
    """
    In-memory heuristic trust scoring engine for adaptive risk-based authentication.
    Computes a score in [0, 100] based on device trust cookies, network telemetry,
    User-Agent fingerprinting, recency, and threat indicators.
    """

    @classmethod
    def evaluate(
        cls, request: Any, user: Any, tenant_security_level: Optional[str] = None
    ) -> Tuple[bool, int, Dict[str, Any]]:
        """
        Evaluates risk telemetry for a login attempt.
        Returns:
            allow_bypass (bool): Whether 2FA prompt can be bypassed.
            score (int): Computed trust score clamped between 0 and 100.
            details (dict): Itemized points and diagnostics.
        """
        tenant = getattr(user, "tenant", None)
        level = (
            tenant_security_level
            or getattr(tenant, "security_level", None)
            or "MEDIUM"
        ).upper()

        # Tier NONE: always bypass 2FA immediately
        if level == "NONE":
            return (
                True,
                100,
                {
                    "score": 100,
                    "tenant_security_level": "NONE",
                    "reason": "Tenant security policy NONE permits direct single-factor login.",
                },
            )

        score = 0
        details: Dict[str, Any] = {
            "tenant_security_level": level,
            "factors": {},
        }

        client_ip = get_client_ip(request)
        user_agent = request.META.get("HTTP_USER_AGENT", "") if request else ""
        trust_cookie = (
            request.COOKIES.get("device_trust_token") if hasattr(request, "COOKIES") else None
        )

        prior_sessions = UserSession.objects.filter(user=user)
        active_sessions = prior_sessions.filter(is_active=True)

        # 1. Device Trust Cookie Token (+40)
        cookie_matched = False
        if trust_cookie:
            token_hash = hashlib.sha256(trust_cookie.encode("utf-8")).hexdigest()
            matching_session = active_sessions.filter(trust_hash=token_hash).first()

            if matching_session:
                ttl_days = tenant.device_trust_ttl_days if tenant else 30
                if ttl_days > 0:
                    expiration_cutoff = timezone.now() - timedelta(days=ttl_days)
                    if matching_session.last_activity >= expiration_cutoff:
                        score += 40
                        cookie_matched = True
                        details["factors"]["device_trust_cookie"] = {
                            "points": 40,
                            "session_id": matching_session.id,
                        }
                    else:
                        details["factors"]["device_trust_cookie"] = {
                            "points": 0,
                            "reason": "Trust cookie session expired.",
                        }
                else:
                    details["factors"]["device_trust_cookie"] = {
                        "points": 0,
                        "reason": "Device trust disabled for security tier.",
                    }

        # 2 & 3. IP and Subnet Matching (+20 exact, +15 /24 subnet)
        ip_matched = False
        if client_ip:
            if prior_sessions.filter(ip_address=client_ip).exists():
                score += 20
                ip_matched = True
                details["factors"]["ip_exact_match"] = {"points": 20, "ip": client_ip}
            elif "." in client_ip:
                # IPv4 /24 subnet match
                subnet_prefix = ".".join(client_ip.split(".")[:3]) + "."
                if prior_sessions.filter(ip_address__startswith=subnet_prefix).exists():
                    score += 15
                    details["factors"]["subnet_match"] = {
                        "points": 15,
                        "subnet": subnet_prefix + "0/24",
                    }

        # 4. User-Agent Exact Match (+15)
        if user_agent and prior_sessions.filter(user_agent=user_agent).exists():
            score += 15
            details["factors"]["user_agent_match"] = {"points": 15}

        # 5. Activity within last 7 days (+10)
        seven_days_ago = timezone.now() - timedelta(days=7)
        recent_sessions = prior_sessions.filter(last_activity__gte=seven_days_ago)
        if recent_sessions.exists():
            # Check if recent activity is from the same device (UA or trust cookie) or IP
            recency_matched = False
            if client_ip and recent_sessions.filter(ip_address=client_ip).exists():
                recency_matched = True
            elif user_agent and recent_sessions.filter(user_agent=user_agent).exists():
                recency_matched = True
            elif cookie_matched:
                recency_matched = True

            if recency_matched:
                score += 10
                details["factors"]["recent_activity"] = {"points": 10}

        # 6. Operating System / Platform Mismatch (-25)
        current_os = extract_os_family(user_agent)
        if current_os and prior_sessions.exists():
            known_prior_os = set()
            for ua_str in prior_sessions.values_list("user_agent", flat=True)[:20]:
                os_fam = extract_os_family(ua_str)
                if os_fam:
                    known_prior_os.add(os_fam)

            if known_prior_os and current_os not in known_prior_os:
                score -= 25
                details["factors"]["os_mismatch"] = {
                    "points": -25,
                    "current": current_os,
                    "known": list(known_prior_os),
                }

        # 7. Impossible Travel Anomaly (-60)
        is_impossible_travel = False
        if request:
            meta = request.META
            if (
                meta.get("HTTP_X_IMPOSSIBLE_TRAVEL") == "true"
                or meta.get("HTTP_X_IMPOSSIBLE_TRAVEL") == "1"
                or meta.get("HTTP_IMPOSSIBLE_TRAVEL") == "true"
            ):
                is_impossible_travel = True

        if is_impossible_travel:
            score -= 60
            details["factors"]["impossible_travel"] = {"points": -60}

        # 8. Suspicious IP / Datacenter / Tor (-40)
        is_suspicious_ip = False
        if request:
            meta = request.META
            if (
                meta.get("HTTP_X_SUSPICIOUS_IP") == "true"
                or meta.get("HTTP_X_SUSPICIOUS_IP") == "1"
                or meta.get("HTTP_X_THREAT_DETECTED") == "true"
            ):
                is_suspicious_ip = True

        if is_suspicious_ip:
            score -= 40
            details["factors"]["suspicious_ip"] = {"points": -40}

        # Clamp strictly between 0 and 100
        clamped_score = max(0, min(100, score))
        details["raw_score"] = score
        details["score"] = clamped_score

        # Determine 2FA bypass based on tenant threshold
        # HIGH: strictly no bypass regardless of score
        # LOW: threshold 60
        # MEDIUM: threshold 75
        threshold = tenant.trust_score_threshold if tenant else 75
        details["threshold"] = threshold

        if level == "HIGH":
            allow_bypass = False
            details["decision"] = "2FA enforced: HIGH security tier strictly requires MFA."
        else:
            allow_bypass = clamped_score >= threshold
            details["decision"] = (
                f"2FA bypassed: score {clamped_score} >= threshold {threshold}"
                if allow_bypass
                else f"2FA required: score {clamped_score} < threshold {threshold}"
            )

        return (allow_bypass, clamped_score, details)
