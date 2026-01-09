from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt


from django.conf import settings
from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Profile
@method_decorator(csrf_exempt, name="dispatch")
class GoogleLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        token = request.data.get("token")

        if not token:
            raise AuthenticationFailed("Google token missing")

        try:
            idinfo = id_token.verify_oauth2_token(
                token,
                google_requests.Request(),
                settings.GOOGLE_CLIENT_ID,
            )
        except Exception:
            raise AuthenticationFailed("Invalid Google token")

        email = idinfo.get("email")
        name = idinfo.get("name")

        if not email:
            raise AuthenticationFailed("Google account has no email")

        user = User.objects.filter(email=email).first()

        if user:
            profile = user.profile

            # 🔒 BLOCK sellers / brokers / admin
            if profile.role != "client":
                raise AuthenticationFailed(
                    "Google login allowed only for clients"
                )
        else:
            # ✅ Create CLIENT user
            username = email.split("@")[0]

            user = User.objects.create_user(
                username=username,
                email=email,
                password=None,
            )

            Profile.objects.create(
                user=user,
                role="client",
                is_profile_complete=True,
                is_admin_approved=True,
            )

        # 🎟 Issue JWT cookies (same as normal login)
        refresh = RefreshToken.for_user(user)

        response = Response({"role": "client"})

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
