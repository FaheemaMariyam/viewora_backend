from rest_framework import serializers

from ..models import BrokerDetails, Profile, SellerDetails


class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.CharField(source="user.email", read_only=True)

    # Details from Broker/Seller models
    city = serializers.SerializerMethodField()
    area = serializers.SerializerMethodField()
    license_number = serializers.SerializerMethodField()
    certificate = serializers.SerializerMethodField()
    ownership_proof = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = [
            "id",
            "username",
            "email",
            "role",
            "phone_number",
            "is_profile_complete",
            "is_admin_approved",
            "city",
            "area",
            "license_number",
            "certificate",
            "ownership_proof",
        ]

    def get_city(self, obj):
        if obj.role == "seller":
            details = SellerDetails.objects.filter(profile=obj).first()
            return details.city if details else None
        if obj.role == "broker":
            details = BrokerDetails.objects.filter(profile=obj).first()
            return details.city if details else None
        return None

    def get_area(self, obj):
        if obj.role == "seller":
            details = SellerDetails.objects.filter(profile=obj).first()
            return details.area if details else None
        if obj.role == "broker":
            details = BrokerDetails.objects.filter(profile=obj).first()
            return details.area if details else None
        return None

    def get_license_number(self, obj):
        if obj.role == "broker":
            details = BrokerDetails.objects.filter(profile=obj).first()
            return details.license_number if details else None
        return None

    def get_certificate(self, obj):
        if obj.role == "broker":
            details = BrokerDetails.objects.filter(profile=obj).first()
            if details and details.certificate:
                request = self.context.get("request")
                if request:
                    return request.build_absolute_uri(details.certificate.url)
                return details.certificate.url
        return None

    def get_ownership_proof(self, obj):
        if obj.role == "seller":
            details = SellerDetails.objects.filter(profile=obj).first()
            if details and details.ownership_proof:
                request = self.context.get("request")
                if request:
                    return request.build_absolute_uri(details.ownership_proof.url)
                return details.ownership_proof.url
        return None
