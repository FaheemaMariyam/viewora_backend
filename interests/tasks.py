import logging

from celery import shared_task
from django.contrib.auth import get_user_model
from django.db.models import Count

from .models  import PropertyInterest
from notifications.tasks import send_notification_task

logger = logging.getLogger("viewora")
User = get_user_model()



# Triggered when- Client clicks Interested-PropertyInterest is created-Django signal fires-Celery runs this outside the request cycle
# User does NOT wait for logging / notifications,App stays fast,Scales to email, SMS, push notifications later
@shared_task
def interest_created_task(interest_id, property_id, client_id):
    logger.info(
        f"[CELERY] Interest created | "
        f"interest={interest_id} | "
        f"property={property_id} | "
        f"client={client_id}"
    )


# triggered-Automatically on schedule (every X minutes/hours)-No user action needed


# @shared_task
# def pending_interest_reminder():
#     logger.info("[CELERY BEAT] Pending interests reminder running")
@shared_task
def pending_interest_reminder():
    """
    Runs daily.
    Notifies brokers who still have pending interests.
    """
    logger.info("[CELERY BEAT] Running daily pending interest reminder")

    brokers = User.objects.filter(
        profile__role="broker",
        profile__is_admin_approved=True,
    ).annotate(
        pending_count=Count(
            "assigned_interests",
            filter=PropertyInterest.objects.filter(
                status__in=["requested", "assigned"]
            )
        )
    )

    for broker in brokers:
        if broker.pending_count == 0:
            continue

        send_notification_task.delay(
            broker.id,
            "Pending Property Interests",
            f"You have {broker.pending_count} pending client interests. Please review them.",
            {
                "type": "daily_reminder",
                "pending_count": broker.pending_count,
            },
        )

    logger.info("[CELERY BEAT] Daily reminder completed")