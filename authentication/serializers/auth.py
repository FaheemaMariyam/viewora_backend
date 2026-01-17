import re

from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from ..models import BrokerDetails, Profile, SellerDetails
from properties.models import Property


class RegisterSerializer(serializers.ModelSerializer):
    role = serializers.ChoiceField(choices=Profile.ROLE_CHOICES)
    phone_number = serializers.CharField(write_only=True)

    #  Seller fields (optional unless role=seller)
    ownership_proof = serializers.FileField(required=False)

    #  Broker fields (optional unless role=broker)
    license_number = serializers.CharField(required=False)
    certificate = serializers.FileField(required=False)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
            "role",
            "phone_number",
            "ownership_proof",
            "license_number",
            "certificate",
        ]
        extra_kwargs = {"password": {"write_only": True}}

    #  Password validation
    def validate_password(self, value):
        validate_password(value)
        return value

    #  Email uniqueness
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already registered")
        return value

    #  Phone normalization (E.164 compatible with Twilio)
    def validate_phone_number(self, value):
        value = value.replace(" ", "")

        # Accept +91XXXXXXXXXX
        if re.match(r"^\+91[6-9]\d{9}$", value):
            return value

        # Accept 10-digit Indian number
        if re.match(r"^[6-9]\d{9}$", value):
            return f"+91{value}"

        raise serializers.ValidationError(
            "Enter a valid Indian phone number with country code (+91)"
        )

    #  Role-based validation
    def validate(self, data):
        role = data.get("role")

        if role == "seller":
            if not data.get("ownership_proof"):
                raise serializers.ValidationError(
                    {"ownership_proof": "Ownership document is required for seller"}
                )

        if role == "broker":
            if not data.get("license_number"):
                raise serializers.ValidationError(
                    {"license_number": "License number is required for broker"}
                )
            if not data.get("certificate"):
                raise serializers.ValidationError(
                    {"certificate": "Certificate document is required for broker"}
                )

        return data

    #  Create user + profile + related details
    def create(self, validated_data):
        role = validated_data.pop("role")
        phone_number = validated_data.pop("phone_number")

        ownership_proof = validated_data.pop("ownership_proof", None)
        license_number = validated_data.pop("license_number", None)
        certificate = validated_data.pop("certificate", None)

        # Create user
        user = User.objects.create_user(**validated_data)

        # Create profile
        profile = Profile.objects.create(
            user=user,
            role=role,
            phone_number=phone_number,
            is_phone_verified=False,
            is_profile_complete=(role == "client"),
            is_admin_approved=(role == "client"),
        )

        # Create seller details
        if role == "seller":
            SellerDetails.objects.create(
                profile=profile,
                ownership_proof=ownership_proof,
            )

        # Create broker details
        if role == "broker":
            BrokerDetails.objects.create(
                profile=profile,
                license_number=license_number,
                certificate=certificate,
            )

        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
class AdminUserSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source="profile.role", read_only=True)
    is_profile_complete = serializers.BooleanField(source="profile.is_profile_complete", read_only=True)
    is_admin_approved = serializers.BooleanField(source="profile.is_admin_approved", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "is_active",
            "date_joined",
            "role",
            "is_profile_complete",
            "is_admin_approved",
        ]


class AdminPropertySerializer(serializers.ModelSerializer):
    seller_username = serializers.CharField(source="seller.username", read_only=True)
    cover_image = serializers.SerializerMethodField()

    class Meta:
        model = Property
        fields = [
            "id",
            "title",
            "price",
            "city",
            "locality",
            "property_type",
            "status",
            "is_active",
            "view_count",
            "interest_count",
            "created_at",
            "seller_username",
            "cover_image",
        ]

    def get_cover_image(self, obj):
        image = obj.images.first()
        if not image: return None
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(image.image.url)
        return image.image.url



class AdminOTPVerifySerializer(serializers.Serializer):
    username = serializers.CharField()
    otp = serializers.CharField(max_length=6)

    def validate_otp(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("OTP must be numeric")
        return value


class BrokerOTPVerifySerializer(serializers.Serializer):
    username = serializers.CharField()
    otp = serializers.CharField(max_length=6)

    def validate_otp(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("OTP must be numeric")
        return value
