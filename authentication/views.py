from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated,AllowAny
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from .serializers import RegisterSerializer, ProfileSerializer,ChangePasswordSerializer,ResetPasswordConfirmSerializer,ResetPasswordRequestSerializer,LoginSerializer,AdminOTPVerifySerializer
from .models import Profile,PasswordResetOTP,AdminLoginOTP
import random
from django.core.mail import send_mail
from rest_framework.exceptions import AuthenticationFailed,ValidationError
from firebase_admin import auth as firebase_auth
from authentication import firebase_admin  # <-- just importing triggers init

# class RegisterView(APIView):
    
#     def post(self, request):
#         serializer = RegisterSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         return Response(
#             {"message": "Registration successful"},
#             status=status.HTTP_201_CREATED
#         )
class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        #  1. Get Firebase ID token from frontend
        firebase_token = request.data.get("firebase_token")

        if not firebase_token:
            raise ValidationError("Phone verification required")

        #  2. Verify Firebase token
        try:
            decoded_token = firebase_auth.verify_id_token(firebase_token)
            phone_number = decoded_token.get("phone_number")
        except Exception:
            raise ValidationError("Invalid or expired phone verification")

        if not phone_number:
            raise ValidationError("Phone number not found in Firebase token")

        # 3. Prevent duplicate phone registrations
        if Profile.objects.filter(phone_number=phone_number).exists():
            raise ValidationError("Phone number already registered")

        #  4. Prepare data for serializer
        data = request.data.copy()
        data["phone_number"] = phone_number

        serializer = RegisterSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # 5. Generate JWT tokens
        user = User.objects.get(username=data["username"])
        refresh = RefreshToken.for_user(user)

        #  6. Set cookies (secure auth)
        response = Response(
            {"message": "Registration successful"},
            status=status.HTTP_201_CREATED
        )
        response.set_cookie(
            key="access",
            value=str(refresh.access_token),
            httponly=True,
            samesite="Lax",
        )
        response.set_cookie(
            key="refresh",
            value=str(refresh),
            httponly=True,
            samesite="Lax",
        )

        return response

class LoginView(APIView):
    serializer_class = LoginSerializer
    permission_classes = []
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            username=serializer.validated_data["username"],
            password=serializer.validated_data["password"]
        )

        if not user:
            raise AuthenticationFailed("Invalid credentials")
            
        if user.is_superuser:
        # delete old OTPs
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
                {
                    "message": "OTP sent to admin email",
                    "mfa_required": True
                },
                status=status.HTTP_200_OK
            )

        profile = user.profile

        # SELLER & BROKER GATES
        if profile.role in ["seller", "broker"]:
            if not profile.is_profile_complete:
                raise ValidationError("Profile incomplete")

                
            if not profile.is_admin_approved:
                raise ValidationError("Admin approval pending")

                

        refresh = RefreshToken.for_user(user)
        response = Response({"role": profile.role})
        response.set_cookie(
            key="access",
            value=str(refresh.access_token),
            httponly=True,
            samesite="Lax"
        )
        response.set_cookie(
            key="refresh",
            value=str(refresh),
            httponly=True,
            samesite="Lax"
        )
        return response
#fetch current user
class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if user.is_superuser:
            return Response({
                
                "role": "admin",
                "username": user.username,
                "email": user.email
            })

        serializer = ProfileSerializer(user.profile)
        return Response(serializer.data)

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

        # (Optional but recommended) logout user
        response = Response(
            {"message": "Password changed successfully"},
            status=status.HTTP_200_OK
        )
        response.delete_cookie("access")
        response.delete_cookie("refresh")

        return response
    
class ResetPasswordRequestView(APIView):
    serializer_class = ResetPasswordRequestSerializer
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise ValidationError("User with this email does not exist")
            
        # Delete old OTPs
        PasswordResetOTP.objects.filter(user=user).delete()

        # Generate OTP
        otp = str(random.randint(100000, 999999))

        PasswordResetOTP.objects.create(user=user, otp=otp)

        # Send OTP
        send_mail(
            subject="Password Reset OTP",
            message=f"Your password reset OTP is {otp}",
            from_email=None,
            recipient_list=[email],
        )

        return Response(
            {"message": "OTP sent to email"},
            status=status.HTTP_200_OK
        )

class ResetPasswordConfirmView(APIView):
    serializer_class = ResetPasswordConfirmSerializer
    def post(self, request):
        serializer = ResetPasswordConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        otp = serializer.validated_data["otp"]
        new_password = serializer.validated_data["new_password"]

        try:
            user = User.objects.get(email=email)
            otp_obj = PasswordResetOTP.objects.get(user=user, otp=otp)
        except (User.DoesNotExist, PasswordResetOTP.DoesNotExist):
            
            raise ValidationError("Invalid OTP or email")

            

        if otp_obj.is_expired():
            otp_obj.delete()

            raise ValidationError("OTP expired")

           
        # Reset password
        user.set_password(new_password)
        user.save()

        # Delete OTP
        otp_obj.delete()

        return Response(
            {"message": "Password reset successful"},
            status=status.HTTP_200_OK
        )

class AdminOTPVerifyView(APIView):
    serializer_class = AdminOTPVerifySerializer
    permission_classes = []

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
        response.set_cookie("access", str(refresh.access_token), httponly=True)
        response.set_cookie("refresh", str(refresh), httponly=True)
        return response