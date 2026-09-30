import hashlib
import time
from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase, RequestFactory
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import (
    OutstandingToken,
    BlacklistedToken,
)
from auditlog.models import LogEntry

from organizations.models import Tenant, Subscription
from users.models import User, UserSession, UserTwoFactorMethod, UserBackupCode
from users.totp_service import (
    generate_totp_secret,
    generate_totp_code,
    verify_totp_code,
    get_otpauth_uri,
    generate_backup_codes,
    verify_and_consume_backup_code,
)
from users.trust_engine import AdaptiveTrustEngine, parse_device_name


class AdaptiveAuthSessionsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.rf = RequestFactory()
        self.subscription = Subscription.objects.create(name="Enterprise", description="Sub")

        # Tenant with MEDIUM security level by default
        self.tenant_medium = Tenant.objects.create(
            name="Medium Security Tenant",
            subscription=self.subscription,
            is_global=False,
        )

        # Tenant with LOW security level
        self.tenant_low = Tenant.objects.create(
            name="Low Security Tenant",
            subscription=self.subscription,
            security_level="LOW",
            is_global=False,
        )

        # Tenant with HIGH security level
        self.tenant_high = Tenant.objects.create(
            name="High Security Tenant",
            subscription=self.subscription,
            security_level="HIGH",
            is_global=False,
        )

        # Tenant with NONE security level
        self.tenant_none = Tenant.objects.create(
            name="No Security Tenant",
            subscription=self.subscription,
            security_level="NONE",
            is_global=False,
        )

        # Users
        self.password = "StrongPassword123!"
        self.user_medium = User.objects.create_user(
            username="user_medium",
            email="medium@example.com",
            password=self.password,
            tenant=self.tenant_medium,
        )
        self.user_low = User.objects.create_user(
            username="user_low",
            email="low@example.com",
            password=self.password,
            tenant=self.tenant_low,
        )
        self.user_high = User.objects.create_user(
            username="user_high",
            email="high@example.com",
            password=self.password,
            tenant=self.tenant_high,
        )
        self.user_none = User.objects.create_user(
            username="user_none",
            email="none@example.com",
            password=self.password,
            tenant=self.tenant_none,
        )
        self.user_other = User.objects.create_user(
            username="user_other",
            email="other@example.com",
            password=self.password,
            tenant=self.tenant_medium,
        )

    def test_tenant_security_level_defaults_and_properties(self):
        """Tenant defaults to MEDIUM and resolves thresholds and device trust TTLs."""
        new_tenant = Tenant.objects.create(
            name="New Default Tenant",
            subscription=self.subscription,
        )
        self.assertEqual(new_tenant.security_level, "MEDIUM")
        self.assertEqual(new_tenant.trust_score_threshold, 75)
        self.assertEqual(new_tenant.device_trust_ttl_days, 30)

        self.assertEqual(self.tenant_low.trust_score_threshold, 60)
        self.assertEqual(self.tenant_low.device_trust_ttl_days, 60)

        self.assertEqual(self.tenant_high.trust_score_threshold, 101)
        self.assertEqual(self.tenant_high.device_trust_ttl_days, 0)

        self.assertEqual(self.tenant_none.trust_score_threshold, 0)
        self.assertEqual(self.tenant_none.device_trust_ttl_days, 0)

    def test_adaptive_trust_engine_scoring_and_clamping(self):
        """AdaptiveTrustEngine correctly scores factors, applies penalties, and clamps within [0, 100]."""
        # Baseline new device request: 0 points
        req_new = self.rf.post(
            "/api/v1/token/",
            REMOTE_ADDR="198.51.100.5",
            HTTP_USER_AGENT="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        )
        bypass, score, details = AdaptiveTrustEngine.evaluate(req_new, self.user_medium)
        self.assertFalse(bypass)
        self.assertEqual(score, 0)

        # Create prior session for user_medium
        trust_token = "valid_trust_token_abc_123"
        trust_hash = hashlib.sha256(trust_token.encode("utf-8")).hexdigest()
        prior_session = UserSession.objects.create(
            user=self.user_medium,
            refresh_token_jti="jti_prior_session_1",
            device_name="Chrome en Linux",
            trust_hash=trust_hash,
            ip_address="192.168.1.50",
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0",
            is_active=True,
        )

        # Request with matching cookie (+40), matching IP (+20), matching UA (+15), and recent activity (+10) = 85
        req_trusted = self.rf.post(
            "/api/v1/token/",
            REMOTE_ADDR="192.168.1.50",
            HTTP_USER_AGENT="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0",
        )
        req_trusted.COOKIES["device_trust_token"] = trust_token
        bypass, score, details = AdaptiveTrustEngine.evaluate(req_trusted, self.user_medium)
        self.assertEqual(score, 85)
        self.assertTrue(bypass)  # 85 >= 75 (MEDIUM threshold)

        # Same request on LOW security tier -> also bypasses (85 >= 60)
        bypass_low, score_low, _ = AdaptiveTrustEngine.evaluate(
            req_trusted, self.user_medium, tenant_security_level="LOW"
        )
        self.assertTrue(bypass_low)
        self.assertEqual(score_low, 85)

        # Same request on HIGH security tier -> strictly NO bypass regardless of score
        bypass_high, score_high, _ = AdaptiveTrustEngine.evaluate(
            req_trusted, self.user_medium, tenant_security_level="HIGH"
        )
        self.assertFalse(bypass_high)
        self.assertEqual(score_high, 85)

        # Test Subnet match (+15): different IP in same /24 subnet (192.168.1.99) without cookie
        req_subnet = self.rf.post(
            "/api/v1/token/",
            REMOTE_ADDR="192.168.1.99",
            HTTP_USER_AGENT="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0",
        )
        _, score_sub, details_sub = AdaptiveTrustEngine.evaluate(req_subnet, self.user_medium)
        self.assertIn("subnet_match", details_sub["factors"])
        self.assertEqual(details_sub["factors"]["subnet_match"]["points"], 15)

        # Test Impossible Travel penalty (-60)
        req_travel = self.rf.post(
            "/api/v1/token/",
            REMOTE_ADDR="192.168.1.50",
            HTTP_USER_AGENT="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0",
            HTTP_X_IMPOSSIBLE_TRAVEL="true",
        )
        req_travel.COOKIES["device_trust_token"] = trust_token
        bypass_travel, score_travel, _ = AdaptiveTrustEngine.evaluate(req_travel, self.user_medium)
        self.assertFalse(bypass_travel)
        self.assertEqual(score_travel, 25)  # 85 - 60 = 25

        # Test Threat/Suspicious IP penalty (-40) and Clamping to 0
        req_threat = self.rf.post(
            "/api/v1/token/",
            REMOTE_ADDR="10.0.0.1",
            HTTP_USER_AGENT="Unknown UA",
            HTTP_X_SUSPICIOUS_IP="true",
            HTTP_X_IMPOSSIBLE_TRAVEL="true",
        )
        _, score_threat, _ = AdaptiveTrustEngine.evaluate(req_threat, self.user_medium)
        self.assertEqual(score_threat, 0)  # Clamped at 0

    def test_totp_service_rfc6238_generation_and_drift(self):
        """TOTP service generates RFC-compliant 6-digit codes and tolerates ±1 time-step drift."""
        secret = generate_totp_secret()
        self.assertGreaterEqual(len(secret), 16)

        current_time = time.time()
        code_current = generate_totp_code(secret, for_time=current_time)
        self.assertEqual(len(code_current), 6)
        self.assertTrue(code_current.isdigit())

        # Exact time verification succeeds
        self.assertTrue(verify_totp_code(secret, code_current, for_time=current_time))

        # Drift tolerance: 30 seconds ago (-1 step)
        code_past = generate_totp_code(secret, for_time=current_time - 30)
        self.assertTrue(verify_totp_code(secret, code_past, for_time=current_time))

        # Drift tolerance: 30 seconds in future (+1 step)
        code_future = generate_totp_code(secret, for_time=current_time + 30)
        self.assertTrue(verify_totp_code(secret, code_future, for_time=current_time))

        # Beyond tolerance: 90 seconds ago (-3 steps) must fail
        code_expired = generate_totp_code(secret, for_time=current_time - 90)
        self.assertFalse(verify_totp_code(secret, code_expired, for_time=current_time))

        # Invalid codes
        self.assertFalse(verify_totp_code(secret, "999999", for_time=current_time))
        self.assertFalse(verify_totp_code(secret, "", for_time=current_time))

        # URI format
        uri = get_otpauth_uri(secret, "testuser@example.com")
        self.assertTrue(uri.startswith("otpauth://totp/"))
        self.assertIn(f"secret={secret}", uri)

    def test_backup_codes_generation_and_single_use_consumption(self):
        """Backup recovery codes are generated and consumed single-use."""
        codes = generate_backup_codes(8)
        self.assertEqual(len(codes), 8)

        # Store in DB for user
        UserBackupCode.objects.bulk_create(
            [UserBackupCode(user=self.user_medium, code_hash=code_hash) for _, code_hash in codes]
        )

        first_plaintext = codes[0][0]
        # First verification succeeds and consumes code
        self.assertTrue(verify_and_consume_backup_code(self.user_medium, first_plaintext))

        # Second verification with the same code must fail
        self.assertFalse(verify_and_consume_backup_code(self.user_medium, first_plaintext))

        # Other codes remain valid
        second_plaintext = codes[1][0]
        self.assertTrue(verify_and_consume_backup_code(self.user_medium, second_plaintext))

    def test_login_step_1_adaptive_bypass_when_score_exceeds_threshold(self):
        """POST /api/v1/token/ issues tokens and creates UserSession directly when trust score meets threshold."""
        # Establish prior trusted session
        trust_token = "cookie_token_test_123"
        trust_hash = hashlib.sha256(trust_token.encode("utf-8")).hexdigest()
        UserSession.objects.create(
            user=self.user_medium,
            refresh_token_jti="jti_seed_1",
            device_name="Chrome en Linux",
            trust_hash=trust_hash,
            ip_address="127.0.0.1",
            user_agent="TestUserAgent/1.0",
            is_active=True,
        )

        # Set trust cookie on client
        self.client.cookies["device_trust_token"] = trust_token

        with patch("users.views.get_client_ip", return_value="127.0.0.1"):
            response = self.client.post(
                "/api/v1/token/",
                {"username": self.user_medium.username, "password": self.password},
                format="json",
                HTTP_USER_AGENT="TestUserAgent/1.0",
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data.get("requires_2fa"))
        self.assertIn("access", response.data)

        # Session created
        session = UserSession.objects.filter(user=self.user_medium).order_by("-created_at").first()
        self.assertIsNotNone(session)
        self.assertTrue(session.is_active)

    def test_login_step_1_requires_2fa_when_score_below_threshold(self):
        """POST /api/v1/token/ returns requires_2fa=True and dispatches email OTP when score < threshold."""
        with patch("users.views.send_otp_email") as mock_send_email:
            response = self.client.post(
                "/api/v1/token/",
                {"username": self.user_medium.username, "password": self.password},
                format="json",
                REMOTE_ADDR="203.0.113.1",
                HTTP_USER_AGENT="NewBrowser/1.0",
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get("requires_2fa"))
        self.assertIn("email", response.data.get("available_methods", []))
        self.assertNotIn("access", response.data)
        mock_send_email.assert_called_once()

    def test_login_step_1_high_security_tier_strictly_enforces_2fa(self):
        """HIGH security tier always requires 2FA even with a trusted device cookie."""
        trust_token = "high_security_trust_token"
        trust_hash = hashlib.sha256(trust_token.encode("utf-8")).hexdigest()
        UserSession.objects.create(
            user=self.user_high,
            refresh_token_jti="jti_high_seed",
            device_name="Safari en macOS",
            trust_hash=trust_hash,
            ip_address="127.0.0.1",
            user_agent="Safari/17.0",
            is_active=True,
        )

        self.client.cookies["device_trust_token"] = trust_token
        with patch("users.views.send_otp_email"):
            response = self.client.post(
                "/api/v1/token/",
                {"username": self.user_high.username, "password": self.password},
                format="json",
                HTTP_USER_AGENT="Safari/17.0",
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get("requires_2fa"))

    def test_login_step_1_none_security_tier_bypasses_2fa(self):
        """NONE security tier completely bypasses 2FA even on unrecognized new devices."""
        response = self.client.post(
            "/api/v1/token/",
            {"username": self.user_none.username, "password": self.password},
            format="json",
            REMOTE_ADDR="203.0.113.88",
            HTTP_USER_AGENT="BrandNewBrowser/1.0",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data.get("requires_2fa"))
        self.assertIn("access", response.data)

    def test_otp_verify_with_totp_code(self):
        """POST /api/v1/users/auth/otp/verify/ verifies TOTP code and issues JWT tokens."""
        secret = generate_totp_secret()
        UserTwoFactorMethod.objects.create(
            user=self.user_medium,
            method_type="TOTP",
            secret=secret,
            is_active=True,
        )

        code = generate_totp_code(secret)
        response = self.client.post(
            "/api/v1/users/auth/otp/verify/",
            {
                "username": self.user_medium.username,
                "code": code,
                "method": "totp",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

        # Invalid TOTP code fails
        resp_fail = self.client.post(
            "/api/v1/users/auth/otp/verify/",
            {
                "username": self.user_medium.username,
                "code": "000000",
                "method": "totp",
            },
            format="json",
        )
        self.assertEqual(resp_fail.status_code, status.HTTP_400_BAD_REQUEST)

    def test_otp_verify_with_backup_code(self):
        """POST /api/v1/users/auth/otp/verify/ verifies single-use backup code."""
        codes = generate_backup_codes(4)
        UserBackupCode.objects.bulk_create(
            [UserBackupCode(user=self.user_medium, code_hash=code_hash) for _, code_hash in codes]
        )

        plaintext_code = codes[0][0]
        response = self.client.post(
            "/api/v1/users/auth/otp/verify/",
            {
                "username": self.user_medium.username,
                "code": plaintext_code,
                "method": "backup_code",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

        # Re-using the same code must fail
        resp_reused = self.client.post(
            "/api/v1/users/auth/otp/verify/",
            {
                "username": self.user_medium.username,
                "code": plaintext_code,
                "method": "backup_code",
            },
            format="json",
        )
        self.assertEqual(resp_reused.status_code, status.HTTP_400_BAD_REQUEST)

    def test_otp_verify_trust_device_cookie_issuance(self):
        """POST /api/v1/users/auth/otp/verify/ with trust_device=True sets device_trust_token cookie."""
        from django.core.cache import cache

        # Set up email OTP in cache
        cache_key = f"otp_data_{self.user_medium.username.lower()}"
        cache.set(
            cache_key,
            {
                "code": "123456",
                "attempts": 0,
                "user_id": str(self.user_medium.id),
                "username": self.user_medium.username.lower(),
            },
            timeout=300,
        )

        response = self.client.post(
            "/api/v1/users/auth/otp/verify/",
            {
                "username": self.user_medium.username,
                "code": "123456",
                "method": "email",
                "trust_device": True,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("device_trust_token", response.cookies)
        cookie = response.cookies["device_trust_token"]
        self.assertTrue(cookie["httponly"])

        # Check session recorded with trust_hash
        session = UserSession.objects.filter(user=self.user_medium).order_by("-created_at").first()
        self.assertIsNotNone(session.trust_hash)

    def test_user_session_listing_and_is_current_identification(self):
        """GET /api/v1/users/sessions/ lists user sessions and identifies is_current=True."""
        refresh = RefreshToken.for_user(self.user_medium)
        current_jti = str(refresh.get("jti"))

        sess_current = UserSession.objects.create(
            user=self.user_medium,
            refresh_token_jti=current_jti,
            device_name="Current Laptop",
            is_active=True,
        )
        sess_other = UserSession.objects.create(
            user=self.user_medium,
            refresh_token_jti="other_jti_phone",
            device_name="Mobile Phone",
            is_active=True,
        )

        self.client.force_authenticate(user=self.user_medium)
        self.client.cookies["refresh_token"] = str(refresh)

        response = self.client.get("/api/v1/users/sessions/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        sessions_data = response.data if isinstance(response.data, list) else response.data.get("results", [])
        self.assertEqual(len(sessions_data), 2)

        data_current = next(s for s in sessions_data if s["id"] == str(sess_current.id))
        data_other = next(s for s in sessions_data if s["id"] == str(sess_other.id))

        self.assertTrue(data_current["is_current"])
        self.assertFalse(data_other["is_current"])

    def test_user_session_revocation_blacklists_refresh_token(self):
        """POST /api/v1/users/sessions/{id}/revoke/ deactivates session and blacklists token."""
        refresh = RefreshToken.for_user(self.user_medium)
        jti = str(refresh.get("jti"))

        session = UserSession.objects.create(
            user=self.user_medium,
            refresh_token_jti=jti,
            device_name="Remote Device",
            is_active=True,
        )

        self.client.force_authenticate(user=self.user_medium)
        resp_revoke = self.client.post(f"/api/v1/users/sessions/{session.id}/revoke/")
        self.assertEqual(resp_revoke.status_code, status.HTTP_200_OK)

        session.refresh_from_db()
        self.assertFalse(session.is_active)

        # Refresh token must be blacklisted
        self.client.logout()
        self.client.cookies["refresh_token"] = str(refresh)
        resp_refresh = self.client.post("/api/v1/token/refresh/")
        self.assertEqual(resp_refresh.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_session_revoke_others(self):
        """POST /api/v1/users/sessions/revoke_others/ revokes all other sessions."""
        refresh = RefreshToken.for_user(self.user_medium)
        current_jti = str(refresh.get("jti"))

        sess_current = UserSession.objects.create(
            user=self.user_medium,
            refresh_token_jti=current_jti,
            device_name="Current PC",
            is_active=True,
        )
        sess_remote1 = UserSession.objects.create(
            user=self.user_medium,
            refresh_token_jti="remote_jti_1",
            device_name="Remote 1",
            is_active=True,
        )
        sess_remote2 = UserSession.objects.create(
            user=self.user_medium,
            refresh_token_jti="remote_jti_2",
            device_name="Remote 2",
            is_active=True,
        )

        self.client.force_authenticate(user=self.user_medium)
        self.client.cookies["refresh_token"] = str(refresh)

        response = self.client.post("/api/v1/users/sessions/revoke_others/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        sess_current.refresh_from_db()
        sess_remote1.refresh_from_db()
        sess_remote2.refresh_from_db()

        self.assertTrue(sess_current.is_active)
        self.assertFalse(sess_remote1.is_active)
        self.assertFalse(sess_remote2.is_active)

    def test_user_session_cross_user_revocation_denied(self):
        """Users cannot revoke sessions belonging to other accounts (returns 404)."""
        sess_other = UserSession.objects.create(
            user=self.user_other,
            refresh_token_jti="other_user_jti",
            device_name="Other Device",
            is_active=True,
        )

        self.client.force_authenticate(user=self.user_medium)
        response = self.client.post(f"/api/v1/users/sessions/{sess_other.id}/revoke/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        sess_other.refresh_from_db()
        self.assertTrue(sess_other.is_active)

    def test_totp_setup_activate_deactivate_flow(self):
        """Complete TOTP lifecycle: setup -> activate with backup codes -> deactivate."""
        self.client.force_authenticate(user=self.user_medium)

        # 1. Setup
        resp_setup = self.client.post("/api/v1/users/auth/mfa/totp/setup/")
        self.assertEqual(resp_setup.status_code, status.HTTP_200_OK)
        secret = resp_setup.data["secret"]
        self.assertIn("otpauth_uri", resp_setup.data)

        # 2. Activate with valid code
        code = generate_totp_code(secret)
        resp_act = self.client.post(
            "/api/v1/users/auth/mfa/totp/activate/",
            {"code": code},
            format="json",
        )
        self.assertEqual(resp_act.status_code, status.HTTP_200_OK)
        self.assertIn("detail", resp_act.data)
        self.assertEqual(resp_act.data["detail"], "TOTP authenticator activated successfully.")
        self.assertEqual(len(resp_act.data["backup_codes"]), 8)

        # Status check
        resp_status = self.client.get("/api/v1/users/auth/mfa/status/")
        self.assertEqual(resp_status.status_code, status.HTTP_200_OK)
        self.assertTrue(resp_status.data["totp_active"])
        self.assertEqual(resp_status.data["backup_codes_remaining"], 8)
        methods = [m["method_type"] for m in resp_status.data["methods"]]
        self.assertIn("TOTP", methods)
        self.assertIn("BACKUP_CODES", methods)

        # 3. Deactivate with password
        resp_deact = self.client.post(
            "/api/v1/users/auth/mfa/totp/deactivate/",
            {"password": self.password},
            format="json",
        )
        self.assertEqual(resp_deact.status_code, status.HTTP_200_OK)

        # Verify removal
        self.assertFalse(
            UserTwoFactorMethod.objects.filter(user=self.user_medium, method_type="TOTP").exists()
        )
        self.assertFalse(UserBackupCode.objects.filter(user=self.user_medium).exists())

    def test_auditlog_records_created(self):
        """UserSession, UserTwoFactorMethod, and UserBackupCode create AuditLog entries."""
        session = UserSession.objects.create(
            user=self.user_medium,
            refresh_token_jti="jti_audit_test",
            device_name="Audit PC",
            is_active=True,
        )
        audit_session = LogEntry.objects.filter(
            object_pk=str(session.id),
            action=LogEntry.Action.CREATE,
        ).first()
        self.assertIsNotNone(audit_session)

        mfa_method = UserTwoFactorMethod.objects.create(
            user=self.user_medium,
            method_type="TOTP",
            secret="SECRET",
            is_active=True,
        )
        audit_mfa = LogEntry.objects.filter(
            object_pk=str(mfa_method.id),
            action=LogEntry.Action.CREATE,
        ).first()
        self.assertIsNotNone(audit_mfa)

    @patch("users.views.send_otp_email")
    def test_login_step_1_metadata_and_totp_email_suppression(self, mock_send_email):
        """Step 1 returns allow_device_trust and device_trust_ttl_days; suppresses email when primary is TOTP."""
        # Enable TOTP for user
        UserTwoFactorMethod.objects.create(
            user=self.user_medium,
            method_type="TOTP",
            secret="TESTSECRET",
            is_active=True,
        )

        resp = self.client.post(
            "/api/v1/token/",
            {"username": self.user_medium.username, "password": self.password},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data["requires_2fa"])
        self.assertEqual(resp.data["primary_method"], "totp")
        self.assertTrue(resp.data["allow_device_trust"])
        self.assertEqual(resp.data["device_trust_ttl_days"], 30)
        # Verify email was NOT sent
        mock_send_email.assert_not_called()

    def test_otp_verify_returns_device_trusted(self):
        """OTPVerifyView returns device_trusted: true when trust is granted, false otherwise."""
        # 1. High security tenant - trust_device requested but policy forbids it
        from users.totp_service import generate_totp_code
        secret = "JBSWY3DPEHPK3PXP"
        UserTwoFactorMethod.objects.create(
            user=self.user_high,
            method_type="TOTP",
            secret=secret,
            is_active=True,
        )
        code = generate_totp_code(secret)
        resp_high = self.client.post(
            "/api/v1/users/auth/otp/verify/",
            {
                "username": self.user_high.username,
                "code": code,
                "method": "totp",
                "trust_device": True,
            },
            format="json",
        )
        self.assertEqual(resp_high.status_code, status.HTTP_200_OK)
        self.assertIn("device_trusted", resp_high.data)
        self.assertFalse(resp_high.data["device_trusted"])

        # 2. Medium security tenant - trust_device requested and allowed
        UserTwoFactorMethod.objects.create(
            user=self.user_medium,
            method_type="TOTP",
            secret=secret,
            is_active=True,
        )
        code_med = generate_totp_code(secret)
        resp_med = self.client.post(
            "/api/v1/users/auth/otp/verify/",
            {
                "username": self.user_medium.username,
                "code": code_med,
                "method": "totp",
                "trust_device": True,
            },
            format="json",
        )
        self.assertEqual(resp_med.status_code, status.HTTP_200_OK)
        self.assertIn("device_trusted", resp_med.data)
        self.assertTrue(resp_med.data["device_trusted"])

