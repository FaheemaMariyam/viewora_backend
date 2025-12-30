from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from interests.models import PropertyInterest
from .models import ChatMessage
from django.shortcuts import  get_object_or_404
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


class ChatHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, interest_id):
        interest = get_object_or_404(PropertyInterest, id=interest_id)

        if request.user not in [interest.client, interest.broker]:
            return Response({"detail": "Forbidden"}, status=403)

        messages = ChatMessage.objects.filter(
            interest=interest
        ).order_by("created_at")

        return Response([
            {
                "id": msg.id,
                "sender": msg.sender.username,
                "message": msg.message,
                "time": msg.created_at.isoformat(),  #  FIXED
                "is_read": msg.is_read,
            }
            for msg in messages
        ])
class MarkMessagesReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, interest_id):
        interest = get_object_or_404(PropertyInterest, id=interest_id)

        if request.user not in [interest.client, interest.broker]:
            return Response({"detail": "Forbidden"}, status=403)

        unread_messages = ChatMessage.objects.filter(
            interest=interest,
            is_read=False
        ).exclude(sender=request.user)

        message_ids = list(
            unread_messages.values_list("id", flat=True)
        )

        unread_messages.update(is_read=True)

        #  REAL-TIME PUSH (ONLY IF NEEDED)
        if message_ids:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"interest_{interest_id}",
                {
                    "type": "read_receipt",
                    "message_ids": message_ids,
                }
            )

        return Response({"status": "ok"})