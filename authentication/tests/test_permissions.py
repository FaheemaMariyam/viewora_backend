from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIRequestFactory

from authentication.models import Profile
from authentication.permissions import IsApprovedBroker, IsApprovedSeller, IsClientUser

factory = APIRequestFactory()


class PermissionTest(TestCase):

    def test_approved_seller_allowed(self):
        user = User.objects.create_user("seller", "pass")
        Profile.objects.create(user=user, role="seller", is_admin_approved=True)

        request = factory.get("/")
        request.user = user

        self.assertTrue(IsApprovedSeller().has_permission(request, None))

    def test_unapproved_broker_denied(self):
        user = User.objects.create_user("broker", "pass")
        Profile.objects.create(user=user, role="broker", is_admin_approved=False)

        request = factory.get("/")
        request.user = user

        self.assertFalse(IsApprovedBroker().has_permission(request, None))

    def test_client_user_allowed(self):
        user = User.objects.create_user("client", "pass")
        Profile.objects.create(user=user, role="client")

        request = factory.get("/")
        request.user = user

        self.assertTrue(IsClientUser().has_permission(request, None))
