from django.test import TestCase
from django.contrib.auth import get_user_model

from authentication.models import Profile
from interests.models import PropertyInterest
from properties.models import Property
from chat.models import ChatMessage

User = get_user_model()


class ChatMessageModelTest(TestCase):

    def test_chat_message_creation(self):
        seller = User.objects.create_user("seller", password="pass")
        Profile.objects.create(user=seller, role="seller", is_admin_approved=True)

        client = User.objects.create_user("client", password="pass")
        Profile.objects.create(user=client, role="client")

        prop = Property.objects.create(
            seller=seller,
            title="House",
            description="Nice",
            property_type="house",
            price=1000000,
            area_size=1000,
            city="Kochi",
            locality="Kaloor",
            address="Addr",
        )

        interest = PropertyInterest.objects.create(property=prop, client=client)

        msg = ChatMessage.objects.create(
            interest=interest,
            sender=client,
            message="Hello",
        )

        self.assertEqual(str(msg), f"{client} → Interest {interest.id}")
        self.assertFalse(msg.is_read)
