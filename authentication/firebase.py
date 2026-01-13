import os

import firebase_admin
from django.conf import settings
from firebase_admin import credentials, messaging

if not firebase_admin._apps:
    cred = credentials.Certificate(
        os.path.join(
            settings.BASE_DIR,
            "firebase/viewora-notification-firebase-adminsdk-fbsvc-c369f555cf.json",
        )
    )
    firebase_admin.initialize_app(cred)


def send_push_notification(token, title, body, data=None):
    if not token:
        return

    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        token=token,
        data=data or {},
    )

    messaging.send(message)
