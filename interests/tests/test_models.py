from django.contrib.auth.models import User
from django.test import TestCase

from authentication.models import Profile
from interests.models import PropertyInterest
from properties.models import Property


class PropertyInterestModelTest(TestCase):

    def test_interest_creation_and_str(self):
        seller = User.objects.create_user("seller", "pass")
        Profile.objects.create(
            user=seller, role="seller", is_admin_approved=True, is_profile_complete=True
        )

        client = User.objects.create_user("client", "pass")
        Profile.objects.create(user=client, role="client")

        prop = Property.objects.create(
            seller=seller,
            title="House",
            description="Nice",
            property_type="house",
            price=1000000,
            area_size=1000,
            city="Kochi",
            locality="Kaloor",
            address="Addr",
        )

        interest = PropertyInterest.objects.create(property=prop, client=client)

        self.assertEqual(interest.status, "requested")
        self.assertIn("House", str(interest))
