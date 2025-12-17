from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from .serializers import RegisterSerializer, ProfileSerializer,ChangePasswordSerializer,ResetPasswordConfirmSerializer,ResetPasswordRequestSerializer,LoginSerializer
from .models import Profile,PasswordResetOTP
import random
from django.core.mail import send_mail
class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"message": "Registration successful"},
            status=status.HTTP_201_CREATED
        )

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
            return Response(
                {"error": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # ✅ SUPERUSER → ADMIN
        if user.is_superuser:
            refresh = RefreshToken.for_user(user)
            response = Response({"role": "admin"})
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

        profile = user.profile

        # 🔒 SELLER & BROKER GATES
        if profile.role in ["seller", "broker"]:
            if not profile.is_profile_complete:
                return Response(
                    {"error": "Profile incomplete"},
                    status=status.HTTP_403_FORBIDDEN
                )
            if not profile.is_admin_approved:
                return Response(
                    {"error": "Admin approval pending"},
                    status=status.HTTP_403_FORBIDDEN
                )

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
            return Response(
                {"error": "Old password is incorrect"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Set new password
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
            return Response(
                {"error": "User with this email does not exist"},
                status=status.HTTP_404_NOT_FOUND
            )

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
            return Response(
                {"error": "Invalid OTP or email"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if otp_obj.is_expired():
            otp_obj.delete()
            return Response(
                {"error": "OTP expired"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Reset password
        user.set_password(new_password)
        user.save()

        # Delete OTP
        otp_obj.delete()

        return Response(
            {"message": "Password reset successful"},
            status=status.HTTP_200_OK
        )
