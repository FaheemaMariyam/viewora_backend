from rest_framework import serializers
from .models import Property

class PropertyCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Property
        exclude = (
            'id',
            'seller',
            'status',
            'view_count',
            'interest_count',
            'created_at',
            'updated_at',
        )
class PropertyListSerializer(serializers.ModelSerializer):
    seller = serializers.StringRelatedField()

    class Meta:
        model = Property
        fields = [
            'id',
            'seller',
            'title',
            'price',
            'city',
            'locality',
            'property_type',
            'area_size',
            'area_unit',
            'bedrooms',
            'bathrooms',
            'view_count',
            'interest_count',
            'created_at',
        ]

