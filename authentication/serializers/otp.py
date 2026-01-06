import re

from rest_framework import serializers


class SendPhoneOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField()

    def validate_phone_number(self, value):
        value = value.replace(" ", "")

        # Accept +91XXXXXXXXXX (E.164 format)
        if re.match(r"^\+91[6-9]\d{9}$", value):
            return value

        # Accept 10-digit Indian number
        if re.match(r"^[6-9]\d{9}$", value):
            return f"+91{value}"

        raise serializers.ValidationError(
            "Enter a valid Indian phone number with country code (+91)"
        )


class VerifyPhoneOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    otp = serializers.CharField(max_length=6)

    def validate_phone_number(self, value):
        value = value.replace(" ", "")

        # Accept +91XXXXXXXXXX (E.164 format)
        if re.match(r"^\+91[6-9]\d{9}$", value):
            return value

        # Accept 10-digit Indian number
        if re.match(r"^[6-9]\d{9}$", value):
            return f"+91{value}"

        raise serializers.ValidationError(
            "Enter a valid Indian phone number with country code (+91)"
        )

    def validate_otp(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("OTP must be numeric")
        return value
