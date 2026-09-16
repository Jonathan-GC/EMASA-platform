from unittest.mock import patch
from django.urls import reverse
from django.core.cache import cache
from django.test import override_settings
from rest_framework.test import APITestCase
from rest_framework import status
from users.models import User


@override_settings(
    DATABASES={
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    }
)
class TwoFactorAuthTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(
            username="otpuser",
            email="otpuser@example.com",
            password="securepassword123",
            name="OTP",
            last_name="User",
            is_active=True,
        )
        self.user2 = User.objects.create_user(
            username="otheruser",
            email="otheruser@example.com",
            password="securepassword456",
            name="Other",
            last_name="User",
            is_active=True,
        )
        self.login_step1_url = reverse("cookie_token_obtain_pair")
        self.otp_request_url = reverse("otp-request")
        self.otp_verify_url = reverse("otp-verify")

    def tearDown(self):
        cache.clear()

    @patch("users.views.send_otp_email")
    def test_login_step1_password_valid_triggers_2fa(self, mock_send_email):
        response = self.client.post(
            self.login_step1_url,
            {"username": "otpuser", "password": "securepassword123"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get("requires_2fa"))
        self.assertEqual(response.data.get("username"), "otpuser")
        self.assertEqual(response.data.get("email"), "otpuser@example.com")
        self.assertNotIn("access", response.data)
        self.assertNotIn("refresh_token", response.cookies)

        # Cache check
        cache_data = cache.get("otp_data_otpuser")
        self.assertIsNotNone(cache_data)
        self.assertEqual(len(cache_data["code"]), 6)
        self.assertEqual(cache_data["username"], "otpuser")
        self.assertEqual(cache_data["user_id"], self.user.id)
        mock_send_email.assert_called_once()

    def test_login_step1_invalid_password_returns_401(self):
        response = self.client.post(
            self.login_step1_url,
            {"username": "otpuser", "password": "wrongpassword"},
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIsNone(cache.get("otp_data_otpuser"))

    @patch("users.views.send_otp_email")
    def test_full_2fa_login_flow_success(self, mock_send_email):
        # Step 1: Submit password with username
        res1 = self.client.post(
            self.login_step1_url,
            {"username": "otpuser", "password": "securepassword123"},
        )
        self.assertEqual(res1.status_code, status.HTTP_200_OK)
        username = res1.data["username"]

        # Fetch generated OTP code from cache
        cache_data = cache.get(f"otp_data_{username.lower()}")
        otp_code = cache_data["code"]

        # Step 2: Submit OTP code with username
        res2 = self.client.post(
            self.otp_verify_url,
            {"username": username, "code": otp_code},
        )
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        self.assertIn("access", res2.data)
        self.assertIn("refresh_token", res2.cookies)

        # OTP deleted from cache
        self.assertIsNone(cache.get(f"otp_data_{username.lower()}"))

    @patch("users.views.send_otp_email")
    def test_otp_resend_with_username(self, mock_send_email):
        res = self.client.post(
            self.otp_request_url,
            {"username": "otpuser"},
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["detail"], "Verification code sent to email.")

        cache_data = cache.get("otp_data_otpuser")
        self.assertIsNotNone(cache_data)
        self.assertEqual(cache_data["username"], "otpuser")
        mock_send_email.assert_called_once()

    def test_prevent_cross_account_otp_login(self):
        """Ensure a code generated for User A cannot be used to log in as User B."""
        # Generate code for user1 (otpuser)
        cache.set(
            "otp_data_otpuser",
            {"code": "123456", "attempts": 0, "user_id": self.user.id, "username": "otpuser"},
            timeout=300,
        )

        # User2 (otheruser) tries to use user1's code to login as otheruser
        response = self.client.post(
            self.otp_verify_url,
            {"username": "otheruser", "code": "123456"},
        )
        # otheruser has no OTP requested in cache
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("OTP expired or not requested", response.data["detail"])

        # Even if otheruser has an OTP code, user1's code should fail on otheruser
        cache.set(
            "otp_data_otheruser",
            {"code": "654321", "attempts": 0, "user_id": self.user2.id, "username": "otheruser"},
            timeout=300,
        )
        response2 = self.client.post(
            self.otp_verify_url,
            {"username": "otheruser", "code": "123456"},
        )
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid verification code", response2.data["detail"])

    def test_verify_2fa_invalid_code_decrements_attempts(self):
        cache.set(
            "otp_data_otpuser",
            {"code": "654321", "attempts": 0, "user_id": self.user.id, "username": "otpuser"},
            timeout=300,
        )
        response = self.client.post(
            self.otp_verify_url,
            {"username": "otpuser", "code": "000000"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid verification code. 2 attempt(s) remaining.", response.data["detail"])

    def test_verify_2fa_max_attempts_invalidates_code(self):
        cache.set(
            "otp_data_otpuser",
            {"code": "654321", "attempts": 2, "user_id": self.user.id, "username": "otpuser"},
            timeout=300,
        )
        response = self.client.post(
            self.otp_verify_url,
            {"username": "otpuser", "code": "000000"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Too many invalid attempts", response.data["detail"])
        self.assertIsNone(cache.get("otp_data_otpuser"))
