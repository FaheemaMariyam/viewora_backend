from django.conf import settings
from django.db import models

User = (
    settings.AUTH_USER_MODEL
)  # Django’s configured user model,Safe for future custom user models


class Property(models.Model):

    PROPERTY_TYPE_CHOICES = (
        ("plot", "Plot"),
        ("house", "House"),
        ("flat", "Flat"),
        ("commercial", "Commercial"),
    )

    STATUS_CHOICES = (
        ("published", "Published"),
        ("sold", "Sold"),
        ("archived", "Archived"),
    )

    #  Ownership
    seller = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="properties"
    )

    # Core info
    title = models.CharField(max_length=255)
    description = models.TextField()

    property_type = models.CharField(max_length=20, choices=PROPERTY_TYPE_CHOICES)

    price = models.DecimalField(max_digits=12, decimal_places=2)
    price_negotiable = models.BooleanField(default=True)

    area_size = models.FloatField(help_text="Area size value")
    area_unit = models.CharField(
        max_length=10, choices=(("sqft", "Sqft"), ("cent", "Cent")), default="sqft"
    )

    # Property history (your requirement)
    property_age_years = models.PositiveIntegerField(
        null=True, blank=True, help_text="How many years the property has been used"
    )
    construction_year = models.PositiveIntegerField(null=True, blank=True)
    last_renovated_year = models.PositiveIntegerField(null=True, blank=True)
    ownership_count = models.PositiveIntegerField(default=1)
    reason_for_selling = models.CharField(max_length=255, null=True, blank=True)

    #  Location (smart broker ready)
    city = models.CharField(max_length=100)
    locality = models.CharField(max_length=100)
    address = models.TextField()

    # Enables Map view,Distance calculations,Nearby property search

    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )

    #  Nearby facilities (,used json field for flexibility,No schema migration needed later, AI-friendly in later

    nearby_places = models.JSONField(
        null=True, blank=True, help_text="schools, hospitals, bus stand, metro, etc."
    )

    #  Property features
    bedrooms = models.PositiveIntegerField(null=True, blank=True)
    bathrooms = models.PositiveIntegerField(null=True, blank=True)
    parking_available = models.BooleanField(default=False)
    furnishing_status = models.CharField(max_length=50, null=True, blank=True)
    facing = models.CharField(max_length=20, null=True, blank=True)

    # System fields
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="published"
    )
    is_active = models.BooleanField(default=True)  # soft delete

    view_count = models.PositiveIntegerField(default=0)  # for analytics later
    interest_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.city}"
