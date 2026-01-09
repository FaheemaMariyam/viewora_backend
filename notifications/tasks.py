
from celery import shared_task
from django.contrib.auth import get_user_model
from notifications.models import Notification
from authentication.firebase import send_push_notification

User = get_user_model()

@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=5, retry_kwargs={"max_retries": 3})
def send_notification_task(self, user_id, title, body, data=None):
    try:
        user = User.objects.get(id=user_id)

        # ✅ STORE IN DB
        Notification.objects.create(
            user=user,
            title=title,
            body=body,
            data=data or {},
        )

        # ✅ SEND PUSH
        token = getattr(user.profile, "fcm_token", None)
        if token:
            send_push_notification(
                token=token,
                title=title,
                body=body,
                data=data or {},
            )

    except User.DoesNotExist:
        return
