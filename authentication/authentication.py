from django.contrib.auth.models import AnonymousUser
from rest_framework.exceptions import AuthenticationFailed  # exception raise
from rest_framework_simplejwt.authentication import (  # Token validation,Token decoding,User fetching
    JWTAuthentication,
)


class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        raw_token = request.COOKIES.get("access")

        if not raw_token:
            return (AnonymousUser(), None)

        try:
            validated_token = self.get_validated_token(raw_token)
            user = self.get_user(validated_token)
            return (user, validated_token)
        except AuthenticationFailed:
            return (AnonymousUser(), None)
