# Proposal: Trusted Device MFA Bypass with Threat Guards

## Why

Users who explicitly trust a device for 30/60 days currently face unexpected MFA verification challenges whenever their client IP or network changes. In tenants with `MEDIUM` security (threshold 75), the device trust cookie only contributes +40 points, causing roaming trusted devices to fail the threshold and defeating the utility of device trust.

## What Changes

- Update `AdaptiveTrustEngine.evaluate` so that a verified, unexpired device trust cookie (`cookie_matched`) directly permits 2FA bypass on `LOW` and `MEDIUM` security tiers.
- Enforce strict mandatory MFA overrides:
  - If tenant security tier is `HIGH`, 2FA remains strictly required on every login attempt regardless of device trust.
  - If critical threat indicators are detected (`HTTP_X_IMPOSSIBLE_TRAVEL`, `HTTP_X_SUSPICIOUS_IP`, `HTTP_X_THREAT_DETECTED`), 2FA remains strictly required regardless of device trust.
- Retain standard additive adaptive trust scoring (`clamped_score >= threshold`) for untrusted or unrecognized devices.

## Capabilities

### New Capabilities
<!-- None -->

### Modified Capabilities
- `adaptive-auth-sessions`: Enable direct 2FA bypass for verified trusted devices while strictly enforcing MFA under `HIGH` tenant security policies or critical threat anomalies.

## Impact

- Affected Code: `Monitor_Atlas/users/trust_engine.py` (`AdaptiveTrustEngine.evaluate`)
- Affected Tests: `Monitor_Atlas/tests/test_adaptive_auth_sessions.py`
- APIs: `POST /api/v1/token/` (`CookieTokenObtainPairView`)
