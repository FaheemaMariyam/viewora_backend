from rest_framework import serializers
from .models import PropertyInterest

class PropertyInterestSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyInterest
        fields = "__all__"
        read_only_fields = (
            'client',
            'broker',
            'status',
            'created_at',
            'updated_at',
        )
