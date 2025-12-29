# from channels.generic.websocket import AsyncWebsocketConsumer
# import json

# class ChatConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         await self.accept()
#         await self.send(json.dumps({"message": "WebSocket connected"}))

#     async def disconnect(self, close_code):
#         pass
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from interests.models import PropertyInterest
from .models import ChatMessage
import json

class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.user = self.scope["user"]
        self.interest_id = self.scope["url_route"]["kwargs"]["interest_id"]
        self.room_group_name = f"interest_{self.interest_id}"

        if not self.user.is_authenticated:
            await self.close()
            return

        allowed = await self.is_allowed_user()
        if not allowed:
            await self.close()
            return

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        print("WS USER:", self.scope["user"])
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data.get("message")

        if not message:
            return

        # await self.save_message(message)

        # await self.channel_layer.group_send(
        #     self.room_group_name,
        #     {
        #         "type": "chat_message",
        #         "sender": self.user.username,
        #         "message": message,
        #     }
        # )
        msg = await self.save_message(message)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "id": msg.id,                # ✅ ADD
                "sender": self.user.username,
                "message": msg.message,
                "time": msg.created_at.isoformat(),  # ✅ optional but good
            }
        )


    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    # ---------- helpers ----------

    @sync_to_async
    def is_allowed_user(self):
        try:
            interest = PropertyInterest.objects.get(id=self.interest_id)
            return (
                self.user == interest.client or
                self.user == interest.broker
            )
        except PropertyInterest.DoesNotExist:
            return False

    # @sync_to_async
    # def save_message(self, message):
    #     interest = PropertyInterest.objects.get(id=self.interest_id)
    #     ChatMessage.objects.create(
    #         interest=interest,
    #         sender=self.user,
    #         message=message
    #     )

    @sync_to_async
    def save_message(self, message):
        interest = PropertyInterest.objects.get(id=self.interest_id)
        return ChatMessage.objects.create(
            interest=interest,
            sender=self.user,
            message=message
        )
    async def read_receipt(self, event):
        await self.send(text_data=json.dumps({
            "type": "read_receipt",
            "message_ids": event["message_ids"]
        }))

