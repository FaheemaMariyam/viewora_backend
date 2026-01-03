# from django.db.models.signals import post_save
# from django.dispatch import receiver

# from .models import PropertyInterest
# from .tasks import interest_created_task
# import logging
# logger=logging.getLogger("viewora")
# @receiver(post_save, sender=PropertyInterest)
# def on_interest_created(sender, instance, created, **kwargs):
#     logger.info(f"SIGNAL: Interest created | id={instance.id}")

#     if not created:
#         return

#     # Increment interest count
#     property_obj = instance.property
#     property_obj.interest_count += 1
#     property_obj.save(update_fields=["interest_count"])
#     interest_created_task.delay(
#     instance.id,
#     instance.property.id,
#     instance.client.id,
# )
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import F
import logging

from .models import PropertyInterest
from .tasks import interest_created_task

logger = logging.getLogger("viewora")


@receiver(post_save, sender=PropertyInterest)
def on_interest_created(sender, instance, created, **kwargs):
    if not created:
        return

    logger.info(f"SIGNAL: Interest created | id={instance.id}")

    # increment interest count safely
    property_obj = instance.property
    property_obj.interest_count = F("interest_count") + 1
    property_obj.save(update_fields=["interest_count"])

    # async celery task
    interest_created_task.delay(
        instance.id,
        instance.property.id,
        instance.client.id,
    )
