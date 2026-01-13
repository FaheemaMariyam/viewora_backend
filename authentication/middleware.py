# This middleware authenticates WebSocket connections using JWT, so Django knows which user is connected to the chat
from asgiref.sync import sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from django.db import close_old_connections
from rest_framework_simplejwt.authentication import JWTAuthentication


class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        close_old_connections()
        scope["user"] = await self.get_user(scope)
        return await super().__call__(scope, receive, send)

    @sync_to_async
    def get_user(self, scope):
        try:
            headers = dict(scope.get("headers", []))
            cookie_header = headers.get(b"cookie", b"").decode()

            cookies = {}
            for item in cookie_header.split(";"):
                if "=" in item:
                    k, v = item.strip().split("=", 1)
                    cookies[k] = v

            raw_token = cookies.get("access")
            if not raw_token:
                return AnonymousUser()

            jwt_auth = JWTAuthentication()
            validated_token = jwt_auth.get_validated_token(raw_token)
            return jwt_auth.get_user(validated_token)

        except Exception as e:
            print("WS AUTH ERROR:", e)
            return AnonymousUser()
