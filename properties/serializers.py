from rest_framework import serializers

from interests.models import PropertyInterest

from .models import Property


class PropertyCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Property
        exclude = (  # seller cannot see this
            "id",
            "seller",
            "status",
            "view_count",
            "interest_count",
            "created_at",
            "updated_at",
        )


# class PropertyListSerializer(serializers.ModelSerializer):
#     seller = serializers.StringRelatedField()


#     class Meta:
#         model = Property
#         fields = [
#             'id',
#             'seller',
#             'title',
#             'price',
#             'city',
#             'locality',
#             'property_type',
#             'area_size',
#             'area_unit',
#             'bedrooms',
#             'bathrooms',
#             'view_count',
#             'interest_count',
#             'created_at',
#         ]
class PropertyListSerializer(serializers.ModelSerializer):
    seller = serializers.StringRelatedField()
    is_interested = serializers.SerializerMethodField()  # ✅ ADD

    class Meta:
        model = Property
        fields = [
            "id",
            "seller",
            "title",
            "price",
            "city",
            "locality",
            "property_type",
            "area_size",
            "area_unit",
            "bedrooms",
            "bathrooms",
            "view_count",
            "interest_count",
            "created_at",
            "is_interested",  # ✅ ADD
        ]

    def get_is_interested(self, obj):
        request = self.context.get("request")

        if not request or not request.user.is_authenticated:
            return False

        return PropertyInterest.objects.filter(
            property=obj, client=request.user
        ).exists()


# class PropertyDetailSerializer(serializers.ModelSerializer):
#     seller = serializers.StringRelatedField()

#     class Meta:
#         model = Property
#         fields = "__all__"
# class PropertyDetailSerializer(serializers.ModelSerializer):
#     seller = serializers.StringRelatedField()
#     is_interested = serializers.SerializerMethodField()

#     class Meta:
#         model = Property
#         fields = "__all__"

#     def get_is_interested(self, obj):
#         request = self.context.get("request")
#         if not request or not request.user.is_authenticated:
#             return False

#         return obj.interests.filter(
#             client=request.user
#         ).exists()
# class PropertyDetailSerializer(serializers.ModelSerializer):
#     seller = serializers.StringRelatedField()
#     is_interested = serializers.SerializerMethodField()

#     class Meta:
#         model = Property
#         fields = "__all__"

#     def get_is_interested(self, obj):
#         request = self.context.get("request")
#         if not request or not request.user.is_authenticated:
#             return False


#         return PropertyInterest.objects.filter(
#             property=obj,
#             client=request.user
#         ).exists()
class PropertyDetailSerializer(serializers.ModelSerializer):
    is_interested = serializers.SerializerMethodField()
    active_interest_id = serializers.SerializerMethodField()

    class Meta:
        model = Property
        fields = "__all__"

    def get_is_interested(self, obj):
        user = self.context["request"].user
        return obj.interests.filter(client=user).exists()

    def get_active_interest_id(self, obj):
        user = self.context["request"].user
        interest = obj.interests.filter(client=user).first()
        return interest.id if interest else None
