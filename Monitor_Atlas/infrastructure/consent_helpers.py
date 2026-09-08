import hashlib
import hmac
from typing import Iterable, Union, Any


def canonical_consent_payload(
    device_eui: str,
    tenant_id: Union[str, int],
    version: Union[int, str],
    terms_version: str,
    measurement_ids: Iterable[Any],
    granter_id: Union[str, int, None],
    granted_at_iso: str,
) -> str:
    """
    Constructs a deterministic canonical string representation for device consent signature generation.
    Format:
        {device_eui}|{tenant_id}|{version}|{terms_version}|{sorted_comma_separated_measurement_ids}|{granter_id}|{granted_at_iso}
    """
    sorted_m_ids = sorted([str(m_id) for m_id in measurement_ids if m_id is not None])
    measurements_str = ",".join(sorted_m_ids)
    granter_str = str(granter_id) if granter_id is not None else ""
    return (
        f"{str(device_eui).strip()}|"
        f"{str(tenant_id).strip()}|"
        f"{version}|"
        f"{str(terms_version).strip()}|"
        f"{measurements_str}|"
        f"{granter_str}|"
        f"{str(granted_at_iso).strip()}"
    )


def compute_device_consent_signature(
    device_eui: str = None,
    tenant_id: Union[str, int] = None,
    version: Union[int, str] = None,
    terms_version: str = None,
    measurement_ids: Iterable[Any] = None,
    granter_id: Union[str, int, None] = None,
    granted_at_iso: str = None,
    payload: str = None,
) -> str:
    """
    Computes a 64-character lowercase hexadecimal SHA-256 digest over the canonical consent payload.
    """
    if payload is None:
        payload = canonical_consent_payload(
            device_eui=device_eui,
            tenant_id=tenant_id,
            version=version,
            terms_version=terms_version,
            measurement_ids=measurement_ids if measurement_ids is not None else [],
            granter_id=granter_id,
            granted_at_iso=granted_at_iso,
        )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest().lower()


def verify_device_consent_signature(consent_instance: Any) -> bool:
    """
    Verifies that the stored device_signature on a DeviceConsent instance matches
    the recalculation of its canonical payload digest using constant-time comparison.
    """
    if not consent_instance or not getattr(consent_instance, "device_signature", None):
        return False

    device_eui = getattr(consent_instance.device, "dev_eui", "") if consent_instance.device else ""
    tenant_id = str(consent_instance.tenant_id) if consent_instance.tenant_id else ""
    version = consent_instance.version
    terms_version = consent_instance.terms_version or ""
    
    # Extract IDs of consented measurements
    if hasattr(consent_instance, "consented_measurements"):
        m_ids = list(consent_instance.consented_measurements.values_list("id", flat=True))
    else:
        m_ids = []

    granter_id = str(consent_instance.granted_by_id) if consent_instance.granted_by_id else ""
    granted_at_iso = consent_instance.granted_at.isoformat() if consent_instance.granted_at else ""

    expected_sig = compute_device_consent_signature(
        device_eui=device_eui,
        tenant_id=tenant_id,
        version=version,
        terms_version=terms_version,
        measurement_ids=m_ids,
        granter_id=granter_id,
        granted_at_iso=granted_at_iso,
    )

    return hmac.compare_digest(expected_sig, consent_instance.device_signature.lower())
