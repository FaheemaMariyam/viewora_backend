
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Notification

# class StoreNotificationView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         Notification.objects.create(
#             user=request.user,
#             title=request.data.get("title", ""),
#             body=request.data.get("body", ""),
#             data=request.data.get("data", {}),
#         )
#         return Response({"status": "saved"})
class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Notification.objects.filter(user=request.user).order_by("-created_at")
        return Response([
            {
                "id": n.id,
                "title": n.title,
                "body": n.body,
                "data": n.data,
                "is_read": n.is_read,
                "created_at": n.created_at,
            }
            for n in qs
        ])


class NotificationUnreadCountView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
        return Response({"count": count})


class NotificationMarkReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        Notification.objects.filter(
            user=request.user,
            is_read=False
        ).update(is_read=True)
        return Response({"status": "ok"})