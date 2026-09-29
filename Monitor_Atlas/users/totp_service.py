import base64
import hashlib
import hmac
import secrets
import struct
import time
import urllib.parse
from typing import List, Tuple
from django.utils import timezone


def generate_totp_secret() -> str:
    """
    Generate a 160-bit (20 bytes) cryptographically random Base32-encoded secret.
    Returns uppercase string without padding.
    """
    random_bytes = secrets.token_bytes(20)
    return base64.b32encode(random_bytes).decode("utf-8").rstrip("=").upper()


def _normalize_secret(secret: str) -> bytes:
    """
    Ensure secret is valid Base32 and decode to bytes.
    """
    clean_secret = secret.strip().upper().replace(" ", "")
    padding_needed = (8 - len(clean_secret) % 8) % 8
    padded = clean_secret + ("=" * padding_needed)
    return base64.b32decode(padded, casefold=True)


def generate_totp_code(
    secret: str, time_step: int = 30, digits: int = 6, for_time: float = None
) -> str:
    """
    RFC 6238 TOTP computation using HMAC-SHA1 and dynamic truncation.
    """
    key = _normalize_secret(secret)
    current_time = time.time() if for_time is None else for_time
    counter = int(current_time) // time_step
    counter_bytes = struct.pack(">Q", counter)

    hmac_hash = hmac.new(key, counter_bytes, hashlib.sha1).digest()
    offset = hmac_hash[-1] & 0x0F
    binary_code = struct.unpack(">I", hmac_hash[offset : offset + 4])[0] & 0x7FFFFFFF
    token = binary_code % (10**digits)
    return f"{token:0{digits}d}"


def verify_totp_code(
    secret: str,
    code: str,
    valid_window: int = 1,
    time_step: int = 30,
    for_time: float = None,
) -> bool:
    """
    Verifies TOTP code against secret, tolerating ±valid_window time steps (clock drift).
    Default ±1 step = ±30 seconds drift tolerance.
    """
    if not secret or not code:
        return False

    clean_code = str(code).strip()
    digits = len(clean_code)
    current_time = time.time() if for_time is None else for_time

    for offset in range(-valid_window, valid_window + 1):
        test_time = current_time + (offset * time_step)
        expected_code = generate_totp_code(
            secret, time_step=time_step, digits=digits, for_time=test_time
        )
        if hmac.compare_digest(expected_code, clean_code):
            return True

    return False


def get_otpauth_uri(secret: str, username: str, issuer: str = "EMASA Monitor") -> str:
    """
    Constructs an RFC-compliant otpauth:// URI for authenticator app QR code provisioning.
    """
    clean_secret = secret.strip().upper().replace(" ", "")
    label = f"{urllib.parse.quote(issuer)}:{urllib.parse.quote(username)}"
    query = urllib.parse.urlencode(
        {
            "secret": clean_secret,
            "issuer": issuer,
            "algorithm": "SHA1",
            "digits": 6,
            "period": 30,
        }
    )
    return f"otpauth://totp/{label}?{query}"


def hash_backup_code(code: str) -> str:
    """
    Canonicalizes backup code by stripping hyphens/whitespace and returning SHA-256 hex digest.
    """
    clean_code = code.replace("-", "").strip().upper()
    return hashlib.sha256(clean_code.encode("utf-8")).hexdigest()


def generate_backup_codes(count: int = 8) -> List[Tuple[str, str]]:
    """
    Generates count single-use backup recovery codes.
    Returns list of (plaintext_code, sha256_hash) tuples.
    Plaintext format: XXXX-XXXX for readability.
    """
    codes: List[Tuple[str, str]] = []
    for _ in range(count):
        part1 = secrets.token_hex(2).upper()
        part2 = secrets.token_hex(2).upper()
        plaintext = f"{part1}-{part2}"
        code_hash = hash_backup_code(plaintext)
        codes.append((plaintext, code_hash))
    return codes


def verify_and_consume_backup_code(user, plaintext_code: str) -> bool:
    """
    Verifies plaintext_code against user's unconsumed UserBackupCode records.
    If valid, marks the code as consumed atomically and returns True.
    """
    if not user or not plaintext_code:
        return False

    code_hash = hash_backup_code(plaintext_code)
    unconsumed_codes = user.backup_codes.filter(is_consumed=False)

    for backup_code_obj in unconsumed_codes:
        if hmac.compare_digest(backup_code_obj.code_hash, code_hash):
            backup_code_obj.is_consumed = True
            backup_code_obj.consumed_at = timezone.now()
            backup_code_obj.save(update_fields=["is_consumed", "consumed_at"])
            return True

    return False
