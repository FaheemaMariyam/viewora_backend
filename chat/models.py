from django.conf import settings
from django.db import models

from interests.models import PropertyInterest


class ChatMessage(models.Model):
    interest = models.ForeignKey(
        PropertyInterest, on_delete=models.CASCADE, related_name="messages"
    )
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.sender} → Interest {self.interest.id}"
