from celery import shared_task
import logging

logger = logging.getLogger("viewora")

#Triggered when- Client clicks Interested-PropertyInterest is created-Django signal fires-Celery runs this outside the request cycle
#User does NOT wait for logging / notifications,App stays fast,Scales to email, SMS, push notifications later
@shared_task
def interest_created_task(interest_id, property_id, client_id):
    logger.info(
        f"[CELERY] Interest created | "
        f"interest={interest_id} | "
        f"property={property_id} | "
        f"client={client_id}"
    )
#triggered-Automatically on schedule (every X minutes/hours)-No user action needed

@shared_task
def pending_interest_reminder():
    logger.info("[CELERY BEAT] Pending interests reminder running")