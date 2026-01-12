import logging
from celery import shared_task
from utils.dynamodb import record_property_view

logger = logging.getLogger("viewora")
@shared_task
def record_property_view_task(property_id, city, locality):
    record_property_view(property_id, city, locality)
