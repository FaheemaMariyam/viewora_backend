from django.contrib.auth.models import User
from django.test import TestCase

from authentication.serializers.auth import LoginSerializer, RegisterSerializer


class RegisterSerializerTest(TestCase):

    def test_register_serializer_valid(self):
        data = {
            "username": "newuser",
            "email": "new@test.com",
            "password": "StrongPass123",
            "role": "client",
            "phone_number": "9999999999",
        }

        serializer = RegisterSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()

        self.assertEqual(user.profile.role, "client")
        self.assertEqual(user.profile.phone_number, "9999999999")

    def test_register_serializer_invalid(self):
        data = {"username": "x"}
        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())


class LoginSerializerTest(TestCase):

    def test_login_serializer_valid(self):
        serializer = LoginSerializer(data={"username": "test", "password": "pass"})
        self.assertTrue(serializer.is_valid())

    def test_login_serializer_missing_password(self):
        serializer = LoginSerializer(data={"username": "test"})
        self.assertFalse(serializer.is_valid())
