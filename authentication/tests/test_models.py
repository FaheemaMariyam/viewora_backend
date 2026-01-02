from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from authentication.models import AdminLoginOTP, PasswordResetOTP, Profile


class ProfileModelTest(TestCase):

    def test_profile_creation(self):
        user = User.objects.create_user(username="testuser", password="pass123")
        profile = Profile.objects.create(user=user, role="seller")

        self.assertEqual(profile.role, "seller")
        self.assertFalse(profile.is_admin_approved)
        self.assertFalse(profile.is_profile_complete)

    def test_profile_str(self):
        user = User.objects.create_user("john", "pass")
        profile = Profile.objects.create(user=user, role="client")
        self.assertEqual(str(profile), "john (client)")


class OTPModelTest(TestCase):

    def test_password_reset_otp_expired(self):
        user = User.objects.create_user("otpuser", "pass")
        otp = PasswordResetOTP.objects.create(user=user, otp="123456")

        otp.created_at = timezone.now() - timedelta(minutes=11)
        otp.save()

        self.assertTrue(otp.is_expired())

    def test_admin_login_otp_not_expired(self):
        user = User.objects.create_superuser("admin", "admin@test.com", "pass")
        otp = AdminLoginOTP.objects.create(user=user, otp="654321")

        self.assertFalse(otp.is_expired())
