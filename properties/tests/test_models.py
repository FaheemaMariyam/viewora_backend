
from django.test import TestCase
from django.contrib.auth.models import User
from properties.models import Property

class PropertyModelTest(TestCase):

    def test_property_creation_and_str(self):
        user = User.objects.create_user(
            username="seller",
            password="pass123"
        )

        prop = Property.objects.create(
            seller=user,
            title="Test House",
            description="Nice house",
            property_type="house",
            price=5000000,
            area_size=1200,
            city="Kochi",
            locality="Edappally",
            address="Some address"
        )

        self.assertEqual(str(prop), "Test House - Kochi")
        self.assertEqual(prop.status, "published")
        self.assertTrue(prop.is_active)
