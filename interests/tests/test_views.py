from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from rest_framework import status

from authentication.models import Profile
from properties.models import Property
from interests.models import PropertyInterest

#client create interest
class CreateInterestViewTest(APITestCase):

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

        self.client.force_authenticate(user=self.client_user)

    def test_create_interest_success(self):
        response = self.client.post(
            f"/api/interests/property/{self.property.id}/interest/"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(PropertyInterest.objects.count(), 1)

#Client cannot interest own property
    def test_interest_own_property_denied(self):
        """
        Seller cannot create interest because permission is IsClientUser
        """
        self.client.force_authenticate(user=self.seller)

        response = self.client.post(
            f"/api/interests/property/{self.property.id}/interest/"
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

#broker accept interest
class BrokerAcceptInterestTest(APITestCase):

    def setUp(self):
        self.broker = User.objects.create_user("broker", "pass")
        Profile.objects.create(
            user=self.broker,
            role="broker",
            is_admin_approved=True
        )

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
            title="House",
            description="Desc",
            property_type="house",
            price=3000000,
            area_size=1200,
            city="Kochi",
            locality="Edappally",
            address="Addr"
        )

        self.interest = PropertyInterest.objects.create(
            property=self.property,
            client=self.client_user,
            broker=self.broker,
            status="assigned"
        )

        self.client.force_authenticate(user=self.broker)

    def test_broker_accept_interest(self):
        response = self.client.post(
            f"/api/interests/interest/{self.interest.id}/accept/"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.interest.refresh_from_db()
        self.assertEqual(self.interest.status, "in_progress")

#broker close the deal
class BrokerCloseDealTest(APITestCase):

    def test_close_deal_success(self):
        broker = User.objects.create_user("broker2", "pass")
        Profile.objects.create(
            user=broker,
            role="broker",
            is_admin_approved=True
        )

        seller = User.objects.create_user("seller2", "pass")
        Profile.objects.create(
            user=seller,
            role="seller",
            is_admin_approved=True,
            is_profile_complete=True
        )

        client = User.objects.create_user("client2", "pass")
        Profile.objects.create(user=client, role="client")

        prop = Property.objects.create(
            seller=seller,
            title="Villa",
            description="Desc",
            property_type="house",
            price=5000000,
            area_size=2500,
            city="Kochi",
            locality="Panampilly",
            address="Addr"
        )

        interest = PropertyInterest.objects.create(
            property=prop,
            client=client,
            broker=broker,
            status="in_progress"
        )

        self.client.force_authenticate(user=broker)

        response = self.client.post(
            f"/api/interests/interest/{interest.id}/close/"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        prop.refresh_from_db()
        interest.refresh_from_db()

        self.assertEqual(prop.status, "sold")
        self.assertEqual(interest.status, "closed")
#broker assign interest list
class BrokerAssignedInterestsViewTest(APITestCase):

    def test_assigned_interests_list(self):
        broker = User.objects.create_user("broker3", "pass")
        Profile.objects.create(
            user=broker,
            role="broker",
            is_admin_approved=True
        )

        self.client.force_authenticate(user=broker)

        response = self.client.get("/api/interests/broker/interests/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
