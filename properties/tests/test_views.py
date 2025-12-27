
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from rest_framework import status

from authentication.models import Profile
from properties.models import Property

#Test: seller can create property
class PropertyCreateViewTest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="seller",
            password="pass123"
        )

        Profile.objects.create(
            user=self.user,
            role="seller",
            is_admin_approved=True,
            is_profile_complete=True
        )

        self.client.force_authenticate(user=self.user)

    def test_create_property_success(self):
        response = self.client.post(
            "/api/properties/create/",
            {
                "title": "New Flat",
                "description": "Nice flat",
                "property_type": "flat",
                "price": 3000000,
                "area_size": 900,
                "city": "Kochi",
                "locality": "Kaloor",
                "address": "Some address"
            },
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Property.objects.count(), 1)
  #Test: non-seller cannot create property
    def test_create_property_denied_for_client(self):
        client_user = User.objects.create_user(
            username="client",
            password="pass123"
        )

        Profile.objects.create(
            user=client_user,
            role="client",
            is_admin_approved=True
        )

        self.client.force_authenticate(user=client_user)

        response = self.client.post("/api/properties/create/", {})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
#Test: property list requires authentication
class PropertyListViewTest(APITestCase):

    def test_list_requires_auth(self):
        response = self.client.get("/api/properties/view/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
#Test: list returns only published & active
    def test_list_properties_success(self):
        user = User.objects.create_user("seller2", "pass")
        Profile.objects.create(
            user=user,
            role="seller",
            is_admin_approved=True,
            is_profile_complete=True
        )

        Property.objects.create(
            seller=user,
            title="Published",
            description="ok",
            property_type="house",
            price=1000000,
            area_size=1000,
            city="Kochi",
            locality="Vytilla",
            address="addr",
            status="published",
            is_active=True
        )

        self.client.force_authenticate(user=user)

        response = self.client.get("/api/properties/view/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
