from celery import shared_task
import logging

logger = logging.getLogger("viewora")


@shared_task
def interest_created_task(interest_id, property_id, client_id):
    logger.info(
        f"[CELERY] Interest created | "
        f"interest={interest_id} | "
        f"property={property_id} | "
        f"client={client_id}"
    )
@shared_task
def pending_interest_reminder():
    logger.info("[CELERY BEAT] Pending interests reminder running")