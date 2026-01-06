# from django.contrib.auth.models import User
# from django.test import TestCase

# from authentication.serializers.auth import LoginSerializer, RegisterSerializer


# class RegisterSerializerTest(TestCase):

#     def test_register_serializer_valid(self):
#         data = {
#             "username": "newuser",
#             "email": "new@test.com",
#             "password": "StrongPass123",
#             "role": "client",
#             "phone_number": "9999999999",
#         }

#         serializer = RegisterSerializer(data=data)
#         self.assertTrue(serializer.is_valid())
#         user = serializer.save()

#         self.assertEqual(user.profile.role, "client")
#         self.assertEqual(user.profile.phone_number, "9999999999")

#     def test_register_serializer_invalid(self):
#         data = {"username": "x"}
#         serializer = RegisterSerializer(data=data)
#         self.assertFalse(serializer.is_valid())


# class LoginSerializerTest(TestCase):

#     def test_login_serializer_valid(self):
#         serializer = LoginSerializer(data={"username": "test", "password": "pass"})
#         self.assertTrue(serializer.is_valid())

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile

#     def test_login_serializer_missing_password(self):
#         serializer = LoginSerializer(data={"username": "test"})
#         self.assertFalse(serializer.is_valid())
from django.test import TestCase

from authentication.serializers.auth import (
    LoginSerializer,
    RegisterSerializer,
)


# register serializer
class RegisterSerializerTest(TestCase):

    def test_register_client_valid(self):
        data = {
            "username": "newclient",
            "email": "client@test.com",
            "password": "StrongPass123!",
            "role": "client",
            "phone_number": "9999999999",
        }

        serializer = RegisterSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        user = serializer.save()

        self.assertEqual(user.profile.role, "client")
        self.assertEqual(user.profile.phone_number, "+919999999999")
        self.assertTrue(user.profile.is_admin_approved)
        # seller signup test

    def test_register_seller_valid(self):
        ownership_file = SimpleUploadedFile(
            "ownership.pdf", b"dummy content", content_type="application/pdf"
        )

        data = {
            "username": "seller1",
            "email": "seller@test.com",
            "password": "StrongPass123!",
            "role": "seller",
            "phone_number": "8888888888",
            "ownership_proof": ownership_file,
        }

        serializer = RegisterSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        user = serializer.save()

        self.assertEqual(user.profile.role, "seller")
        self.assertFalse(user.profile.is_admin_approved)
        self.assertEqual(user.profile.phone_number, "+918888888888")

    # broker signup
    def test_register_broker_valid(self):
        certificate_file = SimpleUploadedFile(
            "license.pdf", b"dummy content", content_type="application/pdf"
        )

        data = {
            "username": "broker1",
            "email": "broker@test.com",
            "password": "StrongPass123!",
            "role": "broker",
            "phone_number": "7777777777",
            "license_number": "LIC123456",
            "certificate": certificate_file,
        }

        serializer = RegisterSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        user = serializer.save()

        self.assertEqual(user.profile.role, "broker")
        self.assertFalse(user.profile.is_admin_approved)
        self.assertEqual(user.profile.phone_number, "+917777777777")

    # invalid seller(missing documents)
    def test_register_seller_missing_document(self):
        data = {
            "username": "seller2",
            "email": "seller2@test.com",
            "password": "StrongPass123!",
            "role": "seller",
            "phone_number": "9999999999",
        }

        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("ownership_proof", serializer.errors)

    # invalid broker
    def test_register_broker_missing_license(self):
        data = {
            "username": "broker2",
            "email": "broker2@test.com",
            "password": "StrongPass123!",
            "role": "broker",
            "phone_number": "9999999999",
        }

        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("license_number", serializer.errors)


# login serializer
class LoginSerializerTest(TestCase):

    def test_login_serializer_valid(self):
        serializer = LoginSerializer(data={"username": "test", "password": "pass"})
        self.assertTrue(serializer.is_valid())

    def test_login_serializer_missing_password(self):
        serializer = LoginSerializer(data={"username": "test"})
        self.assertFalse(serializer.is_valid())
