from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def send_notification(new_engineer_id, message):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"user_{new_engineer_id}",
        {
            'type': 'ticket_notification',
            'message': message
        }
    )