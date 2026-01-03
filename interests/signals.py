from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import PropertyInterest


@receiver(post_save, sender=PropertyInterest)
def on_interest_created(sender, instance, created, **kwargs):
    print("🔥 SIGNAL FIRED", instance.id)
    if not created:
        return

    # Increment interest count
    property_obj = instance.property
    property_obj.interest_count += 1
    property_obj.save(update_fields=["interest_count"])
