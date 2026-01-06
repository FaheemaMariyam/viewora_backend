from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from authentication.models import Profile
from properties.models import Property

User = get_user_model()


class BasePropertyTestCase(APITestCase):

    def create_seller(self, username="seller"):
        user = User.objects.create_user(username=username, password="pass123")
        Profile.objects.create(
            user=user,
            role="seller",
            is_admin_approved=True,
            is_profile_complete=True,
        )
        return user

    def create_client(self, username="client"):
        user = User.objects.create_user(username=username, password="pass123")
        Profile.objects.create(
            user=user,
            role="client",
            is_admin_approved=True,
            is_profile_complete=True,
        )
        return user

    def create_property(self, seller, **kwargs):
        defaults = {
            "title": "Test Property",
            "description": "Nice property",
            "property_type": "house",
            "price": 1000000,
            "area_size": 1000,
            "city": "Kochi",
            "locality": "Kaloor",
            "address": "Some address",
            "status": "published",
            "is_active": True,
        }
        defaults.update(kwargs)
        return Property.objects.create(seller=seller, **defaults)


# -------------------------
# CREATE PROPERTY
# -------------------------
class PropertyCreateViewTest(BasePropertyTestCase):

    def test_seller_can_create_property(self):
        seller = self.create_seller()
        self.client.force_authenticate(user=seller)

        response = self.client.post(
            "/api/properties/create/",
            {
                "title": "Flat",
                "description": "Nice",
                "property_type": "flat",
                "price": 3000000,
                "area_size": 900,
                "city": "Kochi",
                "locality": "Kaloor",
                "address": "Some address",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Property.objects.count(), 1)

    def test_client_cannot_create_property(self):
        client = self.create_client()
        self.client.force_authenticate(user=client)

        response = self.client.post("/api/properties/create/", {})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


# -------------------------
# LIST PROPERTIES
# -------------------------
class PropertyListViewTest(BasePropertyTestCase):

    def test_list_requires_authentication(self):
        response = self.client.get("/api/properties/view/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_returns_only_active_published(self):
        seller = self.create_seller()

        self.create_property(seller)
        self.create_property(seller, status="archived", is_active=False)

        self.client.force_authenticate(user=seller)
        response = self.client.get("/api/properties/view/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)


# -------------------------
# PROPERTY DETAIL
# -------------------------
class PropertyDetailViewTest(BasePropertyTestCase):

    def test_property_detail_success(self):
        seller = self.create_seller()
        prop = self.create_property(seller)

        self.client.force_authenticate(user=seller)
        response = self.client.get(f"/api/properties/view/{prop.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_archived_property_returns_404(self):
        seller = self.create_seller()
        prop = self.create_property(
            seller, status="archived", is_active=False
        )

        self.client.force_authenticate(user=seller)
        response = self.client.get(f"/api/properties/view/{prop.id}/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


# -------------------------
# SELLER OWN PROPERTIES
# -------------------------
class SellerPropertyViewsTest(BasePropertyTestCase):

    def test_seller_sees_only_own_properties(self):
        seller1 = self.create_seller("s1")
        seller2 = self.create_seller("s2")

        self.create_property(seller1, title="Mine")
        self.create_property(seller2, title="Not mine")

        self.client.force_authenticate(user=seller1)
        response = self.client.get("/api/properties/seller/my-properties/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "Mine")


# -------------------------
# TOGGLE ARCHIVE
# -------------------------
class SellerPropertyToggleArchiveTest(BasePropertyTestCase):

    def test_toggle_archive(self):
        seller = self.create_seller()
        prop = self.create_property(seller)

        self.client.force_authenticate(user=seller)
        response = self.client.patch(
            f"/api/properties/seller/property/{prop.id}/toggle-archive/"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        prop.refresh_from_db()
        self.assertFalse(prop.is_active)
        self.assertEqual(prop.status, "archived")
