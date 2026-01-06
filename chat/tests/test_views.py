from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from authentication.models import Profile
from interests.models import PropertyInterest
from properties.models import Property
from chat.models import ChatMessage

User = get_user_model()


class ChatViewsTest(APITestCase):

    def setUp(self):
        self.seller = User.objects.create_user("seller", password="pass")
        Profile.objects.create(
            user=self.seller,
            role="seller",
            is_admin_approved=True,
            is_profile_complete=True,
        )

        self.client_user = User.objects.create_user("client", password="pass")
        Profile.objects.create(user=self.client_user, role="client")

        self.property = Property.objects.create(
            seller=self.seller,
            title="Flat",
            description="Nice",
            property_type="flat",
            price=2000000,
            area_size=900,
            city="Kochi",
            locality="Kaloor",
            address="Addr",
        )

        self.interest = PropertyInterest.objects.create(
            property=self.property,
            client=self.client_user,
            broker=self.seller,  # simulate assigned broker
        )

        self.msg = ChatMessage.objects.create(
            interest=self.interest,
            sender=self.client_user,
            message="Hello",
        )

    # -----------------------
    # Chat history
    # -----------------------
    def test_chat_history_success(self):
        self.client.force_authenticate(user=self.client_user)

        response = self.client.get(
            f"/api/chat/interest/{self.interest.id}/history/"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["message"], "Hello")

    def test_chat_history_forbidden(self):
        stranger = User.objects.create_user("stranger", password="pass")
        Profile.objects.create(user=stranger, role="client")

        self.client.force_authenticate(user=stranger)
        response = self.client.get(
            f"/api/chat/interest/{self.interest.id}/history/"
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # -----------------------
    # Mark messages read
    # -----------------------
    def test_mark_messages_read(self):
        self.client.force_authenticate(user=self.seller)

        response = self.client.post(
            f"/api/chat/interest/{self.interest.id}/read/"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.msg.refresh_from_db()
        self.assertTrue(self.msg.is_read)
