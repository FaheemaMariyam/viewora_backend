import random

from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from twilio.rest import Client

from .models import AdminLoginOTP, PasswordResetOTP, PhoneOTP, Profile
from .serializers.auth import (
    AdminOTPVerifySerializer,
    LoginSerializer,
    RegisterSerializer,
)
from .serializers.otp import SendPhoneOTPSerializer, VerifyPhoneOTPSerializer
from .serializers.password import (
    ChangePasswordSerializer,
    ResetPasswordConfirmSerializer,
    ResetPasswordRequestSerializer,
)
from .serializers.profile import ProfileSerializer


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        if not serializer.is_valid():
            print("REGISTER ERRORS:", serializer.errors)
            return Response(serializer.errors, status=400)

        user = serializer.save()
        return Response(
            {
                "message": "Signup success",
                "role": user.profile.role,
                "is_admin_approved": user.profile.is_admin_approved,
                "is_profile_complete": user.profile.is_profile_complete,
            },
            status=201,
        )


class LoginView(APIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    @swagger_auto_schema(request_body=LoginSerializer)
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(
            raise_exception=True
        )  # If the serializer data is invalid, immediately raise an exception instead of returning False
        user = authenticate(
            username=serializer.validated_data["username"],
            password=serializer.validated_data["password"],
        )

        if not user:
            raise AuthenticationFailed("Invalid credentials")

        if user.is_superuser:
            # Old OTPs are deleted, New 6-digit OTP is generated, OTP is emailed,  Login is paused
            AdminLoginOTP.objects.filter(user=user).delete()
            otp = str(random.randint(100000, 999999))
            AdminLoginOTP.objects.create(user=user, otp=otp)

            send_mail(
                subject="Admin Login OTP",
                message=f"Your admin login OTP is {otp}",
                from_email=None,
                recipient_list=[user.email],
            )

            return Response(
                {"message": "OTP sent to admin email", "mfa_required": True},
                status=status.HTTP_200_OK,
            )
        # load profile for non admin users
        profile = user.profile

        # SELLER & BROKER GATES
        if profile.role in ["seller", "broker"]:
            if not profile.is_profile_complete:
                raise ValidationError("Profile incomplete")

            if not profile.is_admin_approved:
                raise ValidationError("Admin approval pending")
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        # Store tokens securely in cookies
        response = Response({"role": profile.role})
        # access token
        response.set_cookie(
            key="access",
            value=str(refresh.access_token),
            httponly=True,
            # samesite="Lax"  #none in production
            samesite="Lax",  # 🔥 CHANGE
            secure=False,
        )
        # refresh token
        response.set_cookie(
            key="refresh",
            value=str(refresh),
            httponly=True,
            # samesite="Lax"
            samesite="Lax",  # 🔥 CHANGE
            secure=False,
        )
        return response


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        profile = user.profile

        if profile.role in ["seller", "broker"] and not profile.is_admin_approved:
            return Response({"error": "Admin approval pending"}, status=403)

        return Response(
            {
                "id": user.id,
                "username": user.username,
                "role": profile.role,
            }
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        response = Response({"message": "Logged out successfully"})
        response.delete_cookie("access")
        response.delete_cookie("refresh")
        return response


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        old_password = serializer.validated_data["old_password"]
        new_password = serializer.validated_data["new_password"]
        #  Verify old password
        if not user.check_password(old_password):
            raise ValidationError("Old password is incorrect")
        user.set_password(new_password)
        user.save()

        response = Response(
            {"message": "Password changed successfully"}, status=status.HTTP_200_OK
        )  # Forces re-login with new password
        response.delete_cookie("access")
        response.delete_cookie("refresh")
        return response


class ResetPasswordRequestView(APIView):
    permission_classes = [AllowAny]
    serializer_class = ResetPasswordRequestSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]

        #  SAFE: does not crash if duplicates exist
        user = User.objects.filter(email=email).first()

        if not user:
            raise ValidationError("User with this email does not exist")

        # delete old OTPs
        PasswordResetOTP.objects.filter(user=user).delete()

        otp = str(random.randint(100000, 999999))
        PasswordResetOTP.objects.create(user=user, otp=otp)

        send_mail(
            subject="Password Reset OTP",
            message=f"Your password reset OTP is {otp}",
            from_email=None,  # uses DEFAULT_FROM_EMAIL
            recipient_list=[email],
        )

        return Response({"message": "OTP sent to email"}, status=status.HTTP_200_OK)


class ResetPasswordConfirmView(APIView):
    permission_classes = [AllowAny]  # 🔥 REQUIRED
    serializer_class = ResetPasswordConfirmSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        otp = serializer.validated_data["otp"]
        new_password = serializer.validated_data["new_password"]

        user = User.objects.filter(email=email).first()
        if not user:
            raise ValidationError("User with this email does not exist")

        otp_obj = PasswordResetOTP.objects.filter(user=user, otp=otp).first()

        if not otp_obj:
            raise ValidationError("Invalid OTP")

        if otp_obj.is_expired():
            otp_obj.delete()
            raise ValidationError("OTP expired")

        # ✅ Reset password
        user.set_password(new_password)
        user.save()

        otp_obj.delete()

        return Response(
            {"message": "Password reset successful"}, status=status.HTTP_200_OK
        )


class AdminOTPVerifyView(APIView):
    serializer_class = AdminOTPVerifySerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data["username"]
        otp = serializer.validated_data["otp"]
        try:
            user = User.objects.get(username=username, is_superuser=True)
            otp_obj = AdminLoginOTP.objects.get(user=user, otp=otp)
        except (User.DoesNotExist, AdminLoginOTP.DoesNotExist):
            raise ValidationError("Invalid OTP")

        if otp_obj.is_expired():
            otp_obj.delete()
            raise ValidationError("OTP expired")
        # OTP valid → issue JWT
        refresh = RefreshToken.for_user(user)
        otp_obj.delete()

        response = Response({"role": "admin"})
        # response.set_cookie("access", str(refresh.access_token), httponly=True)
        # response.set_cookie("refresh", str(refresh), httponly=True)
        response.set_cookie(
            "access",
            str(refresh.access_token),
            httponly=True,
            samesite="Lax",
            secure=False,
        )
        response.set_cookie(
            "refresh", str(refresh), httponly=True, samesite="Lax", secure=False
        )

        return response


# Creates a Twilio client using credentials from settings to communicate with Twilio
client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)


@method_decorator(
    csrf_exempt, name="dispatch"
)  # It disables CSRF protection for this API view,All requests to this view bypass CSRF checks
# This endpoint Is public (AllowAny), Is called from frontend , Does not use session authentication , Uses OTP (not cookies)
class SendPhoneOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # Validate request data using serializer (Swagger-friendly)
        serializer = SendPhoneOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone_number = serializer.validated_data["phone_number"]

        try:  # Uses Twilio Verify service to send an SMS OTP to the given phone number
            client.verify.services(settings.TWILIO_VERIFY_SID).verifications.create(
                to=phone_number, channel="sms"
            )

            return Response(
                {"message": "OTP sent"}, status=status.HTTP_200_OK
            )  # Confirms OTP was sent successfully.

        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(csrf_exempt, name="dispatch")
class VerifyPhoneOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # Validate request data using serializer (Swagger-friendly)
        serializer = VerifyPhoneOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone_number = serializer.validated_data["phone_number"]
        otp = serializer.validated_data["otp"]

        try:  # Uses Twilio Verify to check whether the OTP is correct.
            verification_check = client.verify.services(
                settings.TWILIO_VERIFY_SID
            ).verification_checks.create(to=phone_number, code=otp)

            if (
                verification_check.status == "approved"
            ):  # If Twilio returns approved, the phone number is verified.
                return Response({"verified": True}, status=status.HTTP_200_OK)

            return Response(
                {"error": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
