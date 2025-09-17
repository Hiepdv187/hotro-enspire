from django.db import models
from django.contrib.auth.models import AbstractUser
from PIL import Image
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.conf import settings
import os

from imagekit.models import ProcessedImageField, ImageSpecField
from imagekit.processors import ResizeToFill, Adjust
from django.utils import timezone
from django.core.validators import RegexValidator

def user_directory_path(instance, filename):
    return f'avatars/{filename}'

class User(AbstractUser):
    is_customer = models.BooleanField(default=False)
    is_engineer = models.BooleanField(default=False)
    email = models.EmailField(unique=False)
    username = models.CharField(max_length=1000, unique=True)
    first_name = models.CharField(max_length=20, default='')
    last_name = models.CharField(max_length=100, default='')
    avatar = ProcessedImageField(upload_to=user_directory_path, 
                                 processors=[ResizeToFill(500, 500)], 
                                 format='PNG',  # Đổi từ JPEG sang PNG
                                 options={'quality': 90},
                                 default='avatars/avt.jpg',
                                 blank=True, 
                                 null=True)
    avatar_small = ImageSpecField(source='avatar',
                                  processors=[ResizeToFill(100, 100)],
                                  format='PNG',
                                  options={'quality': 50})
    avatar_medium = ImageSpecField(source='avatar',
                                   processors=[ResizeToFill(500, 500)],
                                   format='PNG',
                                   options={'quality': 90})
    school = models.CharField(max_length=200, null=True)
    PLACES_CHOICES = (
        ('Ban lãnh đạo','Ban lãnh đạo'),
        ('Phòng mầm non 1', 'Phòng mầm non 1'),
        ('Phòng mầm non 2', 'Phòng mầm non 2'),
        ('Phòng mầm non 3', 'Phòng mầm non 3'),
        ('Phòng tiểu học', 'Phòng tiểu học'),
        ('Phòng hành chính', 'Phòng hành chính'),
        ('Ban kiểm soát', 'Ban kiểm soát'),
        ('Phòng kế toán', 'Phòng kế toán'),
        ('Phòng kinh doanh marketing', 'Phòng kinh doanh marketing'),
        ('Phòng nhân sự', 'Phòng nhân sự'),
        ('Học viện Enspire Láng Hạ','Học viện Enspire Láng Hạ'),
        ('Enspire Hải Phòng', 'Enspire Hải Phòng'),
        ('Phòng công nghệ', 'Phòng công nghệ'),
        ('Phòng R&D mầm non', 'Phòng R&D mầm non'),
        
    )
    work_place = models.CharField(max_length=50, choices=PLACES_CHOICES, default='')
    date_of_birth = models.DateField(null=True, blank=True)
    phone_regex = RegexValidator (regex=r'^\+?1?\d{9,15}$', message="Lỗi, hãy nhập lại!")
    phone = models.CharField(validators=[phone_regex], max_length=10, blank=True)
    GENDER_CHOICES = (
        ('Nam', 'Male'),
        ('Nữ', 'Female'),
        ('Khác', 'Other'),
    )
    gender = models.CharField(max_length=4, choices=GENDER_CHOICES, blank=True, null=True)
    title = models.CharField(max_length=1000, default='')
    def get_admin_user(self):
        try:
            admin_user = User.objects.get(is_superuser=True)
            return admin_user
        except User.DoesNotExist:
            return None

@receiver(pre_save, sender=User)
def resize_avatar(sender, instance, **kwargs):
    if instance.avatar and os.path.exists(instance.avatar.path):
        width = 50
        height = 50
        img = Image.open(instance.avatar.path)
        
        # Giữ nguyên mode ảnh gốc (RGBA, RGB, L, v.v.)
        original_mode = img.mode
        
        # Resize ảnh
        img = img.resize((width, height), Image.Resampling.LANCZOS)
        
        # Lưu ảnh với định dạng phù hợp
        if original_mode == 'RGBA':
            img = img.convert('RGBA')
            img.save(instance.avatar.path, 'PNG', quality=90)
        else:
            img = img.convert('RGB')
            img.save(instance.avatar.path, 'JPEG', quality=90)
