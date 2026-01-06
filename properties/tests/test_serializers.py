from django.test import TestCase
from django.contrib.auth import get_user_model

from properties.models import Property
from properties.serializers import PropertyCreateSerializer

User = get_user_model()


class PropertyCreateSerializerTest(TestCase):

    def setUp(self):
        self.seller = User.objects.create_user(
            username="seller",
            password="pass123"
        )

    def test_valid_property_creation(self):
        data = {
            "title": "Villa",
            "description": "Luxury villa",
            "property_type": "house",
            "price": 8000000,
            "area_size": 2000,
            "city": "Trivandrum",
            "locality": "Kowdiar",
            "address": "Address here",
        }

        serializer = PropertyCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        property_obj = serializer.save(seller=self.seller)

        self.assertEqual(property_obj.title, "Villa")
        self.assertEqual(property_obj.seller, self.seller)
        self.assertEqual(property_obj.status, "published")
        self.assertTrue(property_obj.is_active)
        self.assertEqual(property_obj.view_count, 0)
        self.assertEqual(property_obj.interest_count, 0)

    def test_invalid_property_data(self):
        serializer = PropertyCreateSerializer(data={})
        self.assertFalse(serializer.is_valid())
        self.assertIn("title", serializer.errors)
        self.assertIn("price", serializer.errors)
