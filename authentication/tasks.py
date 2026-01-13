from celery import shared_task
from django.contrib.auth import get_user_model

from authentication.firebase import send_push_notification

User = get_user_model()


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=5,
    retry_kwargs={"max_retries": 3},
)
def send_notification_task(self, user_id, title, body, data=None):
    try:
        user = User.objects.get(id=user_id)
        token = user.profile.fcm_token

        if not token:
            return

        send_push_notification(
            token=token,
            title=title,
            body=body,
            data=data or {},
        )
    except User.DoesNotExist:
        return
