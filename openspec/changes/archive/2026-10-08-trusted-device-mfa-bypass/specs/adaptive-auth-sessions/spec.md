## MODIFIED Requirements

### Requirement: Adaptive Device Trust Scoring Engine
The system MUST provide an in-memory `AdaptiveTrustEngine` that evaluates risk telemetry for every login attempt and computes a normalized device trust score bounded within `[0, 100]`.

For 2FA bypass determination:
1. If tenant security level is `HIGH`, the engine MUST strictly enforce multi-factor authentication (`allow_bypass = False`) regardless of device trust or score.
2. If critical threat indicators are detected (impossible travel anomaly or suspicious/threat-flagged client IP), the engine MUST strictly enforce multi-factor authentication (`allow_bypass = False`) regardless of device trust.
3. If an unexpired, valid device trust token cookie (`device_trust_token`) matches an active session (`cookie_matched`), the engine MUST permit 2FA bypass (`allow_bypass = True`), provided neither a `HIGH` security tier nor a critical threat is active.
4. For untrusted or unrecognized devices, the engine MUST evaluate telemetry factors against the tenant's security tier threshold:
   - Valid device trust cookie: +40 points.
   - Exact client IP match: +20 points.
   - /24 Subnet match: +15 points.
   - User-Agent exact match: +15 points.
   - Recency (<7 days): +10 points.
   - Operating system mismatch: -25 points.
   - Impossible travel anomaly: -60 points.
   - Suspicious IP / threat detected: -40 points.
   The score MUST be clamped strictly between 0 and 100. 2FA bypass SHALL be permitted only if the clamped score meets or exceeds the tenant's threshold (`threshold = 60` for `LOW`, `75` for `MEDIUM`).

#### Scenario: Trusted device roaming across IP addresses bypasses 2FA
- GIVEN a tenant configured with `security_level="MEDIUM"`
- AND an incoming login request presenting a valid unexpired device trust token cookie
- AND originating from an unrecognized IP address with no prior session history
- AND without impossible travel or suspicious IP threat flags
- WHEN `AdaptiveTrustEngine` evaluates the request
- THEN the engine MUST grant 2FA bypass (`allow_bypass: true`)
- AND the decision MUST indicate bypass based on trusted device verification.

#### Scenario: Trusted device with critical threat anomaly enforces 2FA
- GIVEN a tenant configured with `security_level="MEDIUM"`
- AND an incoming login request presenting a valid unexpired device trust token cookie
- AND an impossible travel anomaly or threat-flagged IP is detected
- WHEN `AdaptiveTrustEngine` evaluates the request
- THEN the engine MUST reject 2FA bypass (`allow_bypass: false`)
- AND the system MUST require multi-factor verification.

#### Scenario: Trusted device under high security tier enforces 2FA
- GIVEN a tenant configured with `security_level="HIGH"`
- AND an incoming login request presenting a valid unexpired device trust token cookie
- WHEN `AdaptiveTrustEngine` evaluates the request
- THEN the engine MUST reject 2FA bypass (`allow_bypass: false`)
- AND the system MUST require multi-factor verification.

#### Scenario: Maximum trust score computation for recognized device on matching IP
- GIVEN an incoming login request presenting a valid device trust token cookie (+40), an identical client IP address (+20), an identical User-Agent (+15), and recorded activity 2 days ago (+10)
- WHEN `AdaptiveTrustEngine` calculates the trust score
- THEN the system MUST compute an aggregate score of 85
- AND the score MUST exceed the `MEDIUM` tenant threshold (75), allowing 2FA bypass.

#### Scenario: Impossible travel penalty triggers mandatory 2FA
- GIVEN an incoming login request presenting a valid device trust token (+40) but originating from an IP in a location 5,000 km away from a session logged 15 minutes prior
- WHEN `AdaptiveTrustEngine` evaluates the request
- THEN the engine MUST detect an impossible travel anomaly and apply a -60 penalty
- AND the resulting score MUST drop below any bypass threshold
- AND the system MUST enforce 2FA verification.

#### Scenario: Untrusted new device scoring requires 2FA
- GIVEN an incoming login request from a new device without a trust cookie (0), from an unknown IP address (0), and an unseen User-Agent (0)
- WHEN `AdaptiveTrustEngine` evaluates the request
- THEN the calculated trust score MUST be 0
- AND the system MUST enforce 2FA verification across all security tiers except `NONE`.

#### Scenario: Score clamping within valid boundary
- GIVEN an evaluation with severe negative penalties totaling -125 points
- WHEN `AdaptiveTrustEngine` finalizes the score
- THEN the score MUST be clamped to a minimum value of 0.
