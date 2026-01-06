from django.test import TestCase
from django.contrib.auth import get_user_model

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

        prop = serializer.save(seller=self.seller)

        self.assertEqual(prop.title, "Villa")
        self.assertEqual(prop.seller, self.seller)
        self.assertTrue(prop.is_active)
        self.assertEqual(prop.status, "published")

    def test_invalid_property_data(self):
        serializer = PropertyCreateSerializer(data={})
        self.assertFalse(serializer.is_valid())
        self.assertIn("title", serializer.errors)
        self.assertIn("price", serializer.errors)
