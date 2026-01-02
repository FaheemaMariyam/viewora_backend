from django.contrib.auth.models import User
from rest_framework import serializers

# from ..models import Profile
# from django.contrib.auth.password_validation import validate_password


class SendPhoneOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField()


class VerifyPhoneOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    otp = serializers.CharField(max_length=6)
