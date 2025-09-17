import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import async_to_sync, sync_to_async
import redis

r = redis.Redis(host='127.0.0.1', port=6379, db=0)

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        if self.user.is_authenticated:
            self.room_group_name = f"user_{self.user.id}"

            # Thêm người dùng vào nhóm
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )

            # Thêm người dùng vào danh sách online
            await sync_to_async(r.sadd)("online_users", self.user.id)
            await self.accept()

            # Gửi các thông báo chưa đọc từ Redis
            await self.send_stored_notifications()

    async def disconnect(self, close_code):
        if self.user.is_authenticated:
            # Xóa người dùng khỏi nhóm
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

            # Xóa người dùng khỏi danh sách online
            await sync_to_async(r.srem)("online_users", self.user.id)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'ping':
                # Handle ping message (keep-alive)
                await self.send(text_data=json.dumps({'type': 'pong'}))
                return
                
            if message_type == 'notification':
                message = data.get('message', '')
                if self.user.is_authenticated and message:
                    await self.send_notification(message)
                return
                
            # Handle other message types here if needed
            
        except json.JSONDecodeError:
            print("Invalid JSON received")
        except Exception as e:
            print(f"Error processing WebSocket message: {e}")

    async def send_notification(self, message):
        if self.user.is_authenticated:
            notification_data = {
                'type': 'notification',
                'message': message
            }

            # Lưu thông báo trong Redis nếu người dùng không online
            if not await sync_to_async(r.sismember)("online_users", self.user.id):
                await sync_to_async(r.rpush)(f"notifications_{self.user.id}", json.dumps(notification_data))
            else:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'send_notification_to_client',
                        'message': message
                    }
                )

    async def send_notification_to_client(self, event):
        message = event['message']
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'message': message
        }))

    async def send_stored_notifications(self):
        # Lấy thông báo từ Redis và gửi cho người dùng
        notifications = await sync_to_async(r.lrange)(f"notifications_{self.user.id}", 0, -1)
        for notification in reversed(notifications):
            notification_data = json.loads(notification)
            await self.send(text_data=json.dumps(notification_data))
        # Xóa các thông báo đã gửi khỏi Redis
        await sync_to_async(r.delete)(f"notifications_{self.user.id}")
