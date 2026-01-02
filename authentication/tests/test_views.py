from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from authentication.models import Profile


class AuthAPITest(APITestCase):

    def test_register_success(self):
        """
        POST /api/auth/register/
        """
        response = self.client.post(
            "/api/auth/register/",
            {
                "username": "testuser",
                "email": "test@test.com",
                "password": "StrongPass123",
                "role": "client",
                "phone_number": "9999999999",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_login_failure(self):
        """
        POST /api/auth/login/ with wrong credentials
        """
        response = self.client.post(
            "/api/auth/login/",
            {"username": "wrong", "password": "wrong"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_success_client(self):
        """
        Successful login for client role
        """
        user = User.objects.create_user(username="client", password="pass123")

        # 🔧 FIX: profile must be created manually
        Profile.objects.create(
            user=user, role="client", is_profile_complete=True, is_admin_approved=True
        )

        response = self.client.post(
            "/api/auth/login/",
            {"username": "client", "password": "pass123"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.cookies)

    def test_profile_requires_auth(self):
        """
        GET /api/auth/profile/ without authentication
        """
        response = self.client.get("/api/auth/profile/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
