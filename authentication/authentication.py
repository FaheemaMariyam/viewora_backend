from rest_framework_simplejwt.authentication import JWTAuthentication #Token validation,Token decoding,User fetching
from rest_framework.exceptions import AuthenticationFailed #exception raise

class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        raw_token = request.COOKIES.get("access")

        # No cookie , let DRF continue
        if not raw_token:
            return None

        try:
            validated_token = self.get_validated_token(raw_token)
            user = self.get_user(validated_token)
            return (user, validated_token)
        except AuthenticationFailed:
            # swallow auth errors for public endpoints
            return None
#if valid,attatch the user,else unauthenticated