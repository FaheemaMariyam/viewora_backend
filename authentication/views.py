import random

from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated,IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from twilio.rest import Client

from .models import AdminLoginOTP, BrokerLoginOTP, PasswordResetOTP, Profile
from .serializers.auth import (
    AdminOTPVerifySerializer,
    BrokerOTPVerifySerializer,
    LoginSerializer,
    RegisterSerializer,
    AdminUserSerializer,
    AdminPropertySerializer
)
from properties.models import Property
from .serializers.otp import SendPhoneOTPSerializer, VerifyPhoneOTPSerializer
from .serializers.password import (
    ChangePasswordSerializer,
    ResetPasswordConfirmSerializer,
    ResetPasswordRequestSerializer,
)
from .serializers.profile import ProfileSerializer


class RegisterView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(request_body=RegisterSerializer)
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
        if not user.is_active:
            raise AuthenticationFailed("Account is disabled")

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

        try:
            profile = user.profile
        except Profile.DoesNotExist:
            raise ValidationError("User profile not found")
        # SELLER & BROKER GATES
        if profile.role in ["seller", "broker"]:
            if not profile.is_profile_complete:
                raise ValidationError("Profile incomplete")

            if not profile.is_admin_approved:
                raise ValidationError("Admin approval pending")
        if profile.role == "broker":
            BrokerLoginOTP.objects.filter(user=user).delete()

            otp = str(random.randint(100000, 999999))
            BrokerLoginOTP.objects.create(user=user, otp=otp)

            send_mail(
                subject="Broker Login OTP",
                message=f"Your broker login OTP is {otp}",
                from_email=None,
                recipient_list=[user.email],
            )
            return Response(
                {
                    "message": "OTP sent to broker email",
                    "otp_required": True,
                    "role": "broker",
                },
                status=200,
            )

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        # Store tokens securely in cookies
        response = Response({"role": profile.role})
        # access token
        response.set_cookie(
            key="access",
            value=str(refresh.access_token),
            httponly=True,
            samesite="Lax",  # none in production
            secure=False,
        )
        # refresh token
        response.set_cookie(
            key="refresh",
            value=str(refresh),
            httponly=True,
            # samesite="Lax"
            samesite="Lax",  # CHANGE
            secure=False,
        )
        return response


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ProfileSerializer

    @swagger_auto_schema(
        tags=["Profile"],
        operation_summary="Get current user profile",
        security=[{"cookieAuth": []}],
        responses={200: ProfileSerializer, 403: "Forbidden"},
    )
    def get(self, request):
        user = request.user
        
        # Safe profile check (Superusers might not have profile records)
        try:
            profile = user.profile
        except Profile.DoesNotExist:
            profile = None

        if profile and profile.role in ["seller", "broker"]:
            if not profile.is_profile_complete:
                return Response({"error": "Profile incomplete"}, status=403)

            if not profile.is_admin_approved:
                return Response({"error": "Admin approval pending"}, status=403)

        return Response(
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": profile.role if profile else "admin",
                "is_superuser": user.is_superuser,
            }
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=["Authentication"],
        operation_summary="Logout",
        security=[{"cookieAuth": []}],
        responses={200: "Logged out successfully", 401: "Unauthorized"},
    )
    def post(self, request):
        response = Response({"message": "Logged out successfully"})
        response.delete_cookie("access")
        response.delete_cookie("refresh")
        return response


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(request_body=ChangePasswordSerializer)
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        old_password = serializer.validated_data["old_password"]
        new_password = serializer.validated_data["new_password"]
        #  Verify old password
        if not user.check_password(old_password):
            raise ValidationError("Old password is incorrect")
        if old_password == new_password:
            raise ValidationError("New password must be different from old password")

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

    @swagger_auto_schema(request_body=ResetPasswordRequestSerializer)
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]

        #   does not crash if duplicates exist
        user = User.objects.filter(email=email).first()

        if not user:
            return Response({"message": "If account exists, OTP sent"}, status=200)

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
    permission_classes = [AllowAny]
    serializer_class = ResetPasswordConfirmSerializer

    @swagger_auto_schema(request_body=ResetPasswordConfirmSerializer)
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

        # Reset password
        user.set_password(new_password)
        user.save()

        otp_obj.delete()

        return Response(
            {"message": "Password reset successful"}, status=status.HTTP_200_OK
        )


class AdminOTPVerifyView(APIView):
    serializer_class = AdminOTPVerifySerializer
    permission_classes = [AllowAny]

    @swagger_auto_schema(request_body=AdminOTPVerifySerializer)
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
        # OTP valid - issue JWT
        refresh = RefreshToken.for_user(user)
        otp_obj.delete()

        response = Response({"role": "admin"})

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

    @swagger_auto_schema(request_body=SendPhoneOTPSerializer)
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

    @swagger_auto_schema(request_body=VerifyPhoneOTPSerializer)
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


class RefreshTokenView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        tags=["Authentication"],
        operation_summary="Refresh access token",
        responses={200: "New access token issued", 401: "Invalid refresh token"},
    )
    def post(self, request):
        refresh_token = request.COOKIES.get("refresh")

        if not refresh_token:
            raise AuthenticationFailed("Refresh token not found")

        try:
            refresh = RefreshToken(refresh_token)
            if refresh["user_id"] is None:
                raise AuthenticationFailed("Invalid refresh token")

            access_token = str(refresh.access_token)

            response = Response({"message": "Token refreshed"})
            response.set_cookie(
                key="access",
                value=access_token,
                httponly=True,
                samesite="Lax",
                secure=False,  # True in production
            )
            return response

        except Exception as e:
            print("REFRESH ERROR:", e)
            raise AuthenticationFailed("Invalid refresh token")


class SaveFCMTokenView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        token = request.data.get("token")

        if not token:
            return Response({"error": "FCM token missing"}, status=400)

        profile = request.user.profile
        profile.fcm_token = token
        profile.save(update_fields=["fcm_token"])

        return Response({"message": "FCM token saved"})


class BrokerOTPVerifyView(APIView):
    permission_classes = [AllowAny]
    serializer_class = BrokerOTPVerifySerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data["username"]
        otp = serializer.validated_data["otp"]

        try:
            # user = User.objects.get(username=username)
            user = User.objects.get(username=username, profile__role="broker")

            otp_obj = BrokerLoginOTP.objects.get(user=user, otp=otp)
        except:
            raise ValidationError("Invalid OTP")

        if otp_obj.is_expired():
            otp_obj.delete()
            raise ValidationError("OTP expired")

        #  Issue JWT
        refresh = RefreshToken.for_user(user)
        otp_obj.delete()

        response = Response({"role": "broker"})

        response.set_cookie(
            "access",
            str(refresh.access_token),
            httponly=True,
            samesite="Lax",
            secure=False,
        )
        response.set_cookie(
            "refresh",
            str(refresh),
            httponly=True,
            samesite="Lax",
            secure=False,
        )

        return response
class AdminListUsersView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        search = request.query_params.get("search")

        queryset = User.objects.filter(is_superuser=False).select_related("profile")

        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(email__icontains=search) |
                Q(profile__role__icontains=search)
            )

        serializer = AdminUserSerializer(queryset, many=True)
        return Response(serializer.data, status=200)
        

class AdminToggleUserStatusView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, user_id):
        try:
            user = User.objects.get(id=user_id, is_superuser=False)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        user.is_active = not user.is_active
        user.save(update_fields=["is_active"])

        return Response(
            {
                "message": "User status updated",
                "user_id": user.id,
                "is_active": user.is_active,
            },
            status=200,
        )


class AdminDashboardStatsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        # User Distribution
        user_counts = {
            "total": User.objects.count(),
            "client": Profile.objects.filter(role="client").count(),
            "seller": Profile.objects.filter(role="seller").count(),
            "broker": Profile.objects.filter(role="broker").count(),
        }

        # Property Inventory
        property_counts = {
            "total": Property.objects.count(),
            "house": Property.objects.filter(property_type="house").count(),
            "plot": Property.objects.filter(property_type="plot").count(),
        }

        # Locality Demand (Top 5 Cities)
        from django.db.models import Count
        city_stats = Property.objects.values("city").annotate(count=Count("id")).order_by("-count")[:5]

        return Response({
            "users": user_counts,
            "properties": property_counts,
            "city_stats": list(city_stats)
        })

class AdminPropertyListView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        search = request.query_params.get("search")
        queryset = Property.objects.all().select_related("seller").order_by("-created_at")

        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(city__icontains=search) |
                Q(seller__username__icontains=search)
            )

        serializer = AdminPropertySerializer(queryset, many=True, context={"request": request})
        return Response(serializer.data)

class AdminTogglePropertyStatusView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, property_id):
        try:
            prop = Property.objects.get(id=property_id)
        except Property.DoesNotExist:
            return Response({"error": "Property not found"}, status=404)

        prop.is_active = not prop.is_active
        prop.save(update_fields=["is_active"])

        return Response({
            "message": "Property status updated",
            "is_active": prop.is_active
        })
