# record property view analytics in DynamoDB
import logging

from celery import shared_task

from django.db.models import F
from .models import Property
from utils.dynamodb import record_property_view  # dynamodb

logger = logging.getLogger("viewora")


@shared_task
def record_property_view_task(property_id, city, locality):
    # 1. Record in DynamoDB (Existing)
    record_property_view(property_id, city, locality)
    
    # 2. Increment in PostgreSQL (New)
    try:
        Property.objects.filter(id=property_id).update(view_count=F('view_count') + 1)
    except Exception as e:
        logger.error(f"[CELERY] Failed to increment view_count for property {property_id}: {e}")
