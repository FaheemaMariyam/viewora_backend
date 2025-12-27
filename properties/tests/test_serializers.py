
from django.test import TestCase
from django.contrib.auth.models import User
from properties.serializers import PropertyCreateSerializer

class PropertyCreateSerializerTest(TestCase):

    def test_valid_property_data(self):
        data = {
            "title": "Villa",
            "description": "Luxury villa",
            "property_type": "house",
            "price": 8000000,
            "area_size": 2000,
            "city": "Trivandrum",
            "locality": "Kowdiar",
            "address": "Address here"
        }

        serializer = PropertyCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_invalid_property_data(self):
        serializer = PropertyCreateSerializer(data={})
        self.assertFalse(serializer.is_valid())
