# Design: Trusted Device MFA Bypass with Threat Guards

## Context

See [proposal.md](file:///home/weedopc/Projects/EMASA-platform/openspec/changes/trusted-device-mfa-bypass/proposal.md) for background and motivation.
`AdaptiveTrustEngine.evaluate` computes device risk telemetry and decides whether a login requires MFA or can bypass it. Currently, device trust cookies add +40 points, but in `MEDIUM` tier (threshold 75), IP or network changes yield scores of 50-65, preventing bypass on recognized devices.

## Goals / Non-Goals

**Goals:**
- Elevate active, non-expired device trust cookies (`cookie_matched`) to grant direct 2FA bypass on `LOW` and `MEDIUM` security tiers.
- Enforce strict mandatory MFA when tenant security tier is `HIGH`.
- Enforce strict mandatory MFA when critical threat anomalies (`HTTP_X_IMPOSSIBLE_TRAVEL`, `HTTP_X_SUSPICIOUS_IP`, `HTTP_X_THREAT_DETECTED`) are present.
- Retain additive score evaluation (`clamped_score >= threshold`) for untrusted devices.

**Non-Goals:**
- Modifying session tracking or database models (`UserSession`, `Tenant`).
- Changes to TOTP, backup codes, or email verification flows.
- Modifying frontend login UI.

## Decisions

### Decision 1: Direct Bypass with Threat Guard vs. Static Point Boost
- **Chosen**: Check `cookie_matched` after calculating threat indicators. If `cookie_matched` is True, bypass MFA unless `level == "HIGH"` or `has_critical_threat`.
- **Rationale**: Increasing static cookie points (e.g. from +40 to +75) could cause subtle edge case math flaws (e.g., if negative weights like OS mismatch -25 pull it to 50). Treating trusted device verification as an authenticated credential bypass bounded by threat guards clearly expresses the zero-trust security model.
- **Alternatives Considered**:
  - *Boost cookie points to +80*: Vulnerable to unintended interactions if combined with other minor penalties.
  - *Add a separate bypass flag to tenant configuration*: Adds unnecessary schema complexity when tenant security level already governs policy.

### Decision 2: Critical Threat Definition
- **Chosen**: A critical threat is defined as `is_impossible_travel or is_suspicious_ip` (which covers `HTTP_X_IMPOSSIBLE_TRAVEL`, `HTTP_X_SUSPICIOUS_IP`, and `HTTP_X_THREAT_DETECTED`).
- **Rationale**: These indicators represent severe compromise signals (geo-velocity impossibility, Tor/VPN/datacenter IP, or active threat detection) that justify immediate revocation of trusted device privilege.

## Risks / Trade-offs

- **[Risk] Cookie Theft / Session Hijacking**: An attacker stealing the `device_trust_token` cookie could bypass MFA from another machine.
  - *Mitigation*: The cookie is stored as `HttpOnly`, `Secure`, and `SameSite=Lax`. Furthermore, the engine evaluates platform/OS mismatch and impossible travel anomalies. When impossible travel or suspicious IP is triggered, MFA is immediately enforced. Additionally, tenants requiring zero-trust can configure the `HIGH` security level to disable device trust entirely.
- **[Risk] Untrusted Device Regression**: Untrusted devices must still be evaluated against standard thresholds.
  - *Mitigation*: Existing additive heuristic scoring remains completely active for requests where `cookie_matched` is False.

## Migration Plan

No database migrations or deployment steps required. The change is entirely contained within the application runtime logic in `AdaptiveTrustEngine`.
