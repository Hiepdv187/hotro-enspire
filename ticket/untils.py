from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.utils import timezone
from datetime import timedelta

def send_notification(new_engineer_id, message):
    """Send a structured notification payload to the group for a user.

    Try to attach the recently created Notification object (id, read, timestamp)
    if it exists to allow the frontend to merge/update without a reload.
    """
    channel_layer = get_channel_layer()

    payload = {
        'type': 'notification',
        'message': message,
        'timestamp': timezone.now().isoformat()
    }

    # Try to attach Notification DB record if available (created very recently)
    try:
        from .models import Notification
        # look for a recent notification created for this user with matching message
        recent_cutoff = timezone.now() - timedelta(seconds=10)
        notif = Notification.objects.filter(user_id=new_engineer_id, message=message, timestamp__gte=recent_cutoff).order_by('-timestamp').first()
        if notif:
            payload.update({
                'id': notif.id,
                'read': notif.read,
                'timestamp': notif.timestamp.isoformat()
            })
    except Exception:
        # best-effort — if anything fails, still send a minimal payload
        pass

    async_to_sync(channel_layer.group_send)(
        f"user_{new_engineer_id}",
        {
            'type': 'send_notification_to_client',
            'payload': payload
        }
    )