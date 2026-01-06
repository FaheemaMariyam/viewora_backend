from django.contrib.auth import get_user_model
from django.test import TestCase

from properties.models import Property

User = get_user_model()


class PropertyModelTest(TestCase):

    def setUp(self):
        self.seller = User.objects.create_user(username="seller", password="pass123")

    def test_property_creation_defaults(self):
        prop = Property.objects.create(
            seller=self.seller,
            title="Test House",
            description="Nice house",
            property_type="house",
            price=5000000,
            area_size=1200,
            city="Kochi",
            locality="Edappally",
            address="Some address",
        )

        self.assertEqual(str(prop), "Test House - Kochi")
        self.assertEqual(prop.status, "published")
        self.assertTrue(prop.is_active)
        self.assertTrue(prop.price_negotiable)
        self.assertEqual(prop.area_unit, "sqft")
        self.assertEqual(prop.ownership_count, 1)
        self.assertEqual(prop.view_count, 0)
        self.assertEqual(prop.interest_count, 0)

    def test_optional_fields_can_be_empty(self):
        prop = Property.objects.create(
            seller=self.seller,
            title="Empty Fields Test",
            description="Test",
            property_type="plot",
            price=1000000,
            area_size=500,
            city="Kochi",
            locality="Kaloor",
            address="Test address",
        )

        self.assertIsNone(prop.bedrooms)
        self.assertIsNone(prop.bathrooms)
        self.assertIsNone(prop.latitude)
        self.assertIsNone(prop.longitude)
