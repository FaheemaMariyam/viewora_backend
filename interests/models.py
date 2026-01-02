from django.conf import settings
from django.db import models

from properties.models import Property


class PropertyInterest(models.Model):

    STATUS_CHOICES = (
        ("requested", "Requested"),
        ("assigned", "Broker Assigned"),
        ("in_progress", "In Progress"),
        ("closed", "Closed"),
        ("cancelled", "Cancelled"),
    )
    # One property can have many interests, If the property is deleted , all related interests are deleted

    property = models.ForeignKey(
        Property, on_delete=models.CASCADE, related_name="interests"
    )
    # One client can show interest in many properties ,If client account is deleted ,interests removed

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="property_interests",
    )

    broker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_interests",
    )

    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="requested"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("property", "client")

    def __str__(self):
        return f"{self.client} → {self.property} ({self.status})"
