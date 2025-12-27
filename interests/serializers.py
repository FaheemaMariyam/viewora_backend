from rest_framework import serializers
from .models import PropertyInterest

# class PropertyInterestSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = PropertyInterest
#         fields = "__all__"
#         read_only_fields = (
#             'client',
#             'broker',
#             'status',
#             'created_at',
#             'updated_at',
#         )
class PropertyInterestCreateSerializer(serializers.ModelSerializer):  #for later use
    class Meta:
        model = PropertyInterest
        fields = ['property']

class PropertyInterestListSerializer(serializers.ModelSerializer):
    property = serializers.StringRelatedField()
    client = serializers.StringRelatedField()

    class Meta:
        model = PropertyInterest
        fields = [
            'id',
            'property',
            'client',
            'status',
            'created_at'
        ]

