from drf_yasg.utils import swagger_auto_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification


class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=["Notifications"],
        operation_summary="List notifications",
        operation_description="Get notifications for the logged-in user",
        responses={
            200: "List of notifications",
            401: "Unauthorized",
        },
    )
    def get(self, request):
        qs = Notification.objects.filter(user=request.user).order_by("-created_at")
        return Response(
            [
                {
                    "id": n.id,
                    "title": n.title,
                    "body": n.body,
                    "data": n.data,
                    "is_read": n.is_read,
                    "created_at": n.created_at,
                }
                for n in qs
            ]
        )


class NotificationUnreadCountView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=["Notifications"],
        operation_summary="Get unread notification count",
        responses={
            200: "Unread notification count",
            401: "Unauthorized",
        },
    )
    def get(self, request):
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return Response({"count": count})


class NotificationMarkReadView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=["Notifications"],
        operation_summary="Mark notifications as read",
        operation_description="Marks all unread notifications of the logged-in user as read",
        responses={
            200: "Notifications marked as read",
            401: "Unauthorized",
        },
    )
    def post(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(
            is_read=True
        )
        return Response({"status": "ok"})
