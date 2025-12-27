
from django.test import TestCase
from django.contrib.auth.models import User

from authentication.models import Profile
from properties.models import Property
from interests.models import PropertyInterest
from interests.serializers import (
    PropertyInterestCreateSerializer,
    PropertyInterestListSerializer
)

class PropertyInterestSerializerTest(TestCase):

    def setUp(self):
        self.seller = User.objects.create_user("seller", "pass")
        Profile.objects.create(
            user=self.seller,
            role="seller",
            is_admin_approved=True,
            is_profile_complete=True
        )

        self.client_user = User.objects.create_user("client", "pass")
        Profile.objects.create(user=self.client_user, role="client")

        self.property = Property.objects.create(
            seller=self.seller,
            title="Flat",
            description="Desc",
            property_type="flat",
            price=2000000,
            area_size=900,
            city="Kochi",
            locality="Kaloor",
            address="Addr"
        )

    def test_property_interest_create_serializer_valid(self):
        serializer = PropertyInterestCreateSerializer(
            data={"property": self.property.id}
        )
        self.assertTrue(serializer.is_valid())

    def test_property_interest_create_serializer_invalid(self):
        serializer = PropertyInterestCreateSerializer(data={})
        self.assertFalse(serializer.is_valid())

    def test_property_interest_list_serializer(self):
        interest = PropertyInterest.objects.create(
            property=self.property,
            client=self.client_user
        )

        serializer = PropertyInterestListSerializer(interest)
        data = serializer.data

        self.assertIn("property", data)
        self.assertIn("client", data)
        self.assertEqual(data["status"], "requested")
