from rest_framework import serializers

from .models import PropertyInterest


class PropertyInterestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyInterest
        fields = ["property"]


class PropertyInterestListSerializer(serializers.ModelSerializer):

    property = serializers.StringRelatedField()
    client = serializers.StringRelatedField()
    unread_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = PropertyInterest
        fields = ["id", "property", "client", "unread_count", "status", "created_at"]
