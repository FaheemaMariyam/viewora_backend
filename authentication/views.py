from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import RegisterSerializer, ProfileSerializer
from .models import Profile

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
    def post(self, request):
        user = authenticate(
            username=request.data.get("username"),
            password=request.data.get("password")
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
