from rest_framework import serializers

from .models import PropertyInterest


class PropertyInterestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyInterest
        fields = ["property"]


class PropertyInterestListSerializer(serializers.ModelSerializer):
    property = serializers.StringRelatedField()
    client = serializers.StringRelatedField()
    broker_name = serializers.CharField(source="broker.first_name", read_only=True)
    unread_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = PropertyInterest
        fields = [
            "id",
            "property",
            "client",
            "broker_name",
            "unread_count",
            "status",
            "created_at",
            "updated_at",
        ]
