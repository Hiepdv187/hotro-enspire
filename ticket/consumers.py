import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import async_to_sync, sync_to_async
from django.utils import timezone
from tkt.supabase_client import (
    add_online_user, 
    remove_online_user, 
    is_user_online,
    store_pending_notification,
    get_pending_notifications,
    clear_pending_notifications
)


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

            # Thêm người dùng vào danh sách online (Supabase)
            await sync_to_async(add_online_user)(self.user.id)
            await self.accept()

            # Gửi các thông báo chưa đọc từ Supabase
            await self.send_stored_notifications()

    async def disconnect(self, close_code):
        if self.user.is_authenticated:
            # Xóa người dùng khỏi nhóm
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

            # Xóa người dùng khỏi danh sách online (Supabase)
            await sync_to_async(remove_online_user)(self.user.id)

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
            # Kiểm tra user online qua Supabase
            user_online = await sync_to_async(is_user_online)(self.user.id)
            
            if not user_online:
                # Lưu thông báo vào DB và Supabase nếu người dùng không online
                try:
                    from .models import Notification
                    notif = await sync_to_async(Notification.objects.create)(
                        user_id=self.user.id,
                        message=message,
                        timestamp=timezone.now()
                    )
                    notification_payload = {
                        'type': 'notification',
                        'id': notif.id,
                        'message': message,
                        'read': notif.read,
                        'timestamp': notif.timestamp.isoformat()
                    }
                    # Lưu vào Supabase pending notifications
                    await sync_to_async(store_pending_notification)(self.user.id, notification_payload)
                except Exception as e:
                    print(f"Error storing notification: {e}")
            else:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'send_notification_to_client',
                        'message': message
                    }
                )

    async def send_notification_to_client(self, event):
        # event may contain a structured payload (from models) or a simple message
        payload = event.get('payload')
        if payload:
            await self.send(text_data=json.dumps(payload))
            return

        message = event.get('message')
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'message': message,
            'timestamp': timezone.now().isoformat()
        }))

    async def send_stored_notifications(self):
        # Lấy thông báo pending từ Supabase và gửi cho người dùng
        pending = await sync_to_async(get_pending_notifications)(self.user.id)
        
        for notification in pending:
            notification_data = {
                'type': 'notification',
                'id': notification.get('notification_id'),
                'message': notification.get('message', ''),
                'read': notification.get('read', False),
                'timestamp': notification.get('timestamp', timezone.now().isoformat())
            }
            await self.send(text_data=json.dumps(notification_data))
        
        # Xóa các thông báo đã gửi khỏi Supabase
        if pending:
            await sync_to_async(clear_pending_notifications)(self.user.id)
