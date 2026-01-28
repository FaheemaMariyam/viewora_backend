import random
from django.core.mail import send_mail
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from .models import BrokerEmailVerificationOTP
from .serializers.auth import (
    BrokerSendEmailOTPSerializer,
    BrokerVerifyEmailOTPSerializer,
)

class SendEmailOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = BrokerSendEmailOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]

        # Remove old OTPs
        BrokerEmailVerificationOTP.objects.filter(email=email).delete()

        otp = str(random.randint(100000, 999999))
        BrokerEmailVerificationOTP.objects.create(email=email, otp=otp)

        send_mail(
            subject="Verify your email",
            message=f"Your email verification OTP is {otp}",
            from_email=None,
            recipient_list=[email],
        )

        return Response({"message": "OTP sent to email"})
class VerifyEmailOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = BrokerVerifyEmailOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        otp = serializer.validated_data["otp"]

        otp_obj = BrokerEmailVerificationOTP.objects.filter(
            email=email, otp=otp
        ).first()

        if not otp_obj:
            raise ValidationError("Invalid OTP")

        if otp_obj.is_expired():
            otp_obj.delete()
            raise ValidationError("OTP expired")

        otp_obj.is_verified = True
        otp_obj.save(update_fields=["is_verified"])

        return Response({"message": "Email verified successfully"})
