import json
from channels.generic.websocket import AsyncWebsocketConsumer


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if self.scope["user"].is_authenticated:
            user_id = self.scope["user"].id
            await self.channel_layer.group_add(
                f'user_{user_id}',  # Sử dụng user ID để đặt tên group
                self.channel_name
            )
            await self.accept()
        else:
            await self.close()

    async def disconnect(self, close_code):
        if self.scope["user"].is_authenticated:
            user_id = self.scope["user"].id
            await self.channel_layer.group_discard(
                f'user_{user_id}',  # Sử dụng user ID để đặt tên group
                self.channel_name
            )

    async def receive(self, text_data):
        if self.scope["user"].is_authenticated:
            text_data_json = json.loads(text_data)
            message = text_data_json.get('message', '')

            await self.send(text_data=json.dumps({
                'message': message
            }))

    async def notification_message(self, message):
        user_id = self.scope["user"].id
        await self.channel_layer.group_send(
            f"user_{user_id}",
            {
                'type': 'notification.message',
                'message': message
            }
        )
        
    async def ticket_notification(self, event):
        message = event['message']
        await self.send(text_data=json.dumps({
            'message': message
        }))