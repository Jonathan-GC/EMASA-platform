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
        self.assertEqual(response.data.get("email"), "otpuser@example.com")
        self.assertNotIn("access", response.data)
        self.assertNotIn("refresh_token", response.cookies)

        # Cache check
        cache_data = cache.get("otp_data_otpuser@example.com")
        self.assertIsNotNone(cache_data)
        self.assertEqual(len(cache_data["code"]), 6)
        mock_send_email.assert_called_once()

    def test_login_step1_invalid_password_returns_401(self):
        response = self.client.post(
            self.login_step1_url,
            {"username": "otpuser", "password": "wrongpassword"},
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIsNone(cache.get("otp_data_otpuser@example.com"))

    @patch("users.views.send_otp_email")
    def test_full_2fa_login_flow_success(self, mock_send_email):
        # Step 1: Submit password
        res1 = self.client.post(
            self.login_step1_url,
            {"username": "otpuser", "password": "securepassword123"},
        )
        self.assertEqual(res1.status_code, status.HTTP_200_OK)
        email = res1.data["email"]

        # Fetch generated OTP code from cache
        cache_data = cache.get(f"otp_data_{email}")
        otp_code = cache_data["code"]

        # Step 2: Submit OTP code
        res2 = self.client.post(
            self.otp_verify_url,
            {"email": email, "code": otp_code},
        )
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        self.assertIn("access", res2.data)
        self.assertIn("refresh_token", res2.cookies)

        # OTP deleted from cache
        self.assertIsNone(cache.get(f"otp_data_{email}"))

    def test_verify_2fa_invalid_code_decrements_attempts(self):
        cache.set(
            "otp_data_otpuser@example.com",
            {"code": "654321", "attempts": 0, "user_id": self.user.id},
            timeout=300,
        )
        response = self.client.post(
            self.otp_verify_url,
            {"email": "otpuser@example.com", "code": "000000"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid verification code. 2 attempt(s) remaining.", response.data["detail"])

    def test_verify_2fa_max_attempts_invalidates_code(self):
        cache.set(
            "otp_data_otpuser@example.com",
            {"code": "654321", "attempts": 2, "user_id": self.user.id},
            timeout=300,
        )
        response = self.client.post(
            self.otp_verify_url,
            {"email": "otpuser@example.com", "code": "000000"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Too many invalid attempts", response.data["detail"])
        self.assertIsNone(cache.get("otp_data_otpuser@example.com"))
