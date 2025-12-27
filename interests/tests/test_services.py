
from django.test import TestCase
from django.contrib.auth.models import User
from authentication.models import Profile
from properties.models import Property
from interests.models import PropertyInterest
from interests.services import assign_broker_to_interest

class AssignBrokerServiceTest(TestCase):

    def test_assigns_first_approved_broker(self):
        broker = User.objects.create_user("broker", "pass")
        Profile.objects.create(
            user=broker,
            role="broker",
            is_admin_approved=True
        )

        seller = User.objects.create_user("seller", "pass")
        Profile.objects.create(
            user=seller,
            role="seller",
            is_admin_approved=True,
            is_profile_complete=True
        )

        client = User.objects.create_user("client", "pass")
        Profile.objects.create(user=client, role="client")

        prop = Property.objects.create(
            seller=seller,
            title="Plot",
            description="Desc",
            property_type="plot",
            price=500000,
            area_size=500,
            city="Kochi",
            locality="Aluva",
            address="Addr"
        )

        interest = PropertyInterest.objects.create(
            property=prop,
            client=client
        )

        assign_broker_to_interest(interest)

        interest.refresh_from_db()

        self.assertEqual(interest.broker, broker)
        self.assertEqual(interest.status, "assigned")
