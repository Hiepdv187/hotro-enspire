from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from django.contrib.auth.models import User
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync, sync_to_async
from django.db.models import Q
import uuid
import json
from django.utils import timezone
from django.contrib.humanize.templatetags.humanize import naturaltime
from channels.generic.websocket import AsyncWebsocketConsumer
from tkt.supabase_client import is_user_online, store_pending_notification

channel_layer = get_channel_layer()

def user_directory_paths(instance, filename):
    unique_id = uuid.uuid4().hex
    ext = filename.split('.')[-1 ]

    new_filename = f'{unique_id}.{ext}'
    return f'media/{new_filename}'

User = get_user_model()
def user_directory_paths(instance, filename):
    return f'media/{filename}'

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    
def send_notification_to_engineer(instance, user_id, message):
    group_name = f"user_{user_id}"

    # Lưu thông báo vào cơ sở dữ liệu Django (PostgreSQL/Supabase)
    notification = Notification.objects.create(
        user_id=user_id,
        message=message,
        timestamp=timezone.now()
    )

    notification_payload = {
        "type": "notification",
        "id": notification.id,
        "message": message,
        "read": notification.read,
        "timestamp": notification.timestamp.isoformat()
    }

    # Kiểm tra user online qua Supabase, nếu offline thì lưu pending notification
    if not is_user_online(user_id):
        # Lưu thông báo pending vào Supabase để gửi khi user online
        store_pending_notification(user_id, notification_payload)
    else:
        # Send structured payload to connected consumers so they get id/timestamp/read
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "send_notification_to_client",
                "payload": notification_payload
            }
        )

class Ticket(models.Model):
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='customer')
    engineer = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name = 'engineer', null=True, blank=True, default = '')
    def get_superusers(self):
        return User.objects.filter(Q(is_superuser=True))
    school = models.CharField(max_length=200, null=True)
    ticket_id = models.CharField(max_length = 15, unique = True)
    ticket_title = models.CharField(max_length = 100)
    ticket_description = models.TextField()
    status = models.CharField(max_length=20, choices=(('Chờ xử lý', 'Chờ xử lý'), ('Đang xử lý', 'Đang xử lý'),('Đã xong', 'Đã xong')), default='Chờ xử lý')
    created_on = models.DateTimeField(auto_now_add = True)
    #last_modified = models.DateTimeField(auto_now=True)
    is_resolved = models.BooleanField(default = False)
    #severity = models.CharField(max_length=5, choices = (('A', 'A'), ('B', 'B')), default = 'B')
    is_assigned_to_engineer = models.BooleanField(default=False, blank=False)
    resolution_steps = models.TextField(blank=True, null = True)
    phone_regex = RegexValidator (regex=r'^\+?1?\d{9,15}$', message="Lỗi, chỉ nhận ký tự là số!")
    phone_number = models.CharField(validators=[phone_regex], max_length=10, blank=True)
    image = models.ImageField (upload_to=user_directory_paths, default=None, blank=True, null=True)
    up_video = models.FileField(upload_to=user_directory_paths, default=None, null=True, blank=True)
    work_as = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='ws', null=True, blank=True, default = '')
    work_place = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='work_place_tickets', null=True, blank=True, default = '')
    
@receiver(post_save, sender=Ticket)
def ticket_status_changed(sender, instance, **kwargs):
    if instance.is_assigned_to_engineer and instance.engineer:
        message = f"Ticket {instance.ticket_id} đã được chuyển cho bạn."
        send_notification_to_engineer(instance, instance.engineer.id, message)

def user_directory_path(instance, filename):
    return f'avatars/{filename}'

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to=user_directory_path, default='avatars/avt.jpg', blank=True, null=True)
    name = models.CharField(max_length=1000, default=None)
    
class CommentAuthor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=1000)
    avatar = models.ImageField(upload_to='avatars/', default='avatars/avt.jpg', blank=True, null=True)

    def __str__(self):
        return self.name

class Comments(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE)
    author = models.ForeignKey(CommentAuthor, on_delete=models.CASCADE, null=True, blank=True)
    body = models.TextField(null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null = True, blank= True)
    created_at = models.DateTimeField(auto_now_add=True)
    parent_comment = models.ForeignKey('self', null=True, blank=True, related_name='replies', on_delete=models.CASCADE)
    image = models.ImageField(upload_to=user_directory_paths, blank=True, null=True)
    def __str__(self):
        return f'Comment by {self.author.name} on {self.ticket.ticket_id}'

class Reply(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE)
    comment = models.ForeignKey(Comments, on_delete=models.CASCADE, related_name='comment_replies')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to=user_directory_paths, blank=True, null=True)
    def __str__(self):
        return f'Reply by {self.author.username} on {self.comment.id}'
    
