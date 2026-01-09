
from django.db.models import F
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from authentication.tasks import send_notification_task
from .models import PropertyInterest
from .tasks import interest_created_task

User = get_user_model()


@receiver(post_save, sender=PropertyInterest)
def on_interest_created(sender, instance, created, **kwargs):
    if not created:
        return

    brokers = User.objects.filter(
        profile__role="broker",
        profile__is_admin_approved=True,
    )

    for broker in brokers:
        send_notification_task.delay(
            broker.id,
            "New Property Interest",
            "A client is interested in a property",
            {"interest_id": str(instance.id)},
        )

    property_obj = instance.property
    property_obj.interest_count = F("interest_count") + 1
    property_obj.save(update_fields=["interest_count"])

    interest_created_task.delay(
        instance.id,
        instance.property.id,
        instance.client.id,
    )
