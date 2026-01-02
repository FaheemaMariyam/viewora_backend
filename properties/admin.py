from django.contrib import admin

from .models import Property


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "property_type",
        "city",
        "status",
        "seller",
        "created_at",
    )
    list_filter = ("property_type", "city", "status")
    search_fields = ("title", "city", "locality")
