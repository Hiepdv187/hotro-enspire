from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone

class Department(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class District(models.Model):
    name = models.CharField(max_length=50)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.name} - {self.department}"

class School(models.Model):
    SCHOOL_STAT_CHOICES = [
        ('Đang liên kết', 'Đang liên kết'),
        ('Đang đàm phán', 'Đang đàm phán'),
        ('Ngưng liên kết', 'Ngưng liên kết'),
    ]
    name = models.CharField(max_length=100)
    school_status = models.CharField(max_length=20, choices=SCHOOL_STAT_CHOICES, default= 'Đang hoạt động')
    school_status_color = models.CharField(max_length=20, default='btn-success')
    school_location = models.CharField(max_length=1000, default = '')
    school_address = models.CharField(max_length=500, default = '')
    district = models.ForeignKey(District, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} - {self.district}"

class LabRoom(models.Model):
    name = models.CharField(max_length=50)
    school = models.ForeignKey(School, on_delete=models.CASCADE, null=True, blank=True)
    district = models.ForeignKey(District, on_delete=models.CASCADE, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.name} - {self.district} - {self.department}"

class Asset(models.Model):
    ASSET_STATUS_CHOICES = [
        ('Tốt', 'Tốt'),
        ('Hỏng', 'Hỏng'),
    ]
    name = models.CharField(max_length=150)
    asset_amount = models.IntegerField(validators= [MinValueValidator(1)], default= 1, null=False)
    asset_status = models.CharField(max_length=10, choices=ASSET_STATUS_CHOICES, default= 'Tốt', null=False)
    school = models.ForeignKey(School, on_delete=models.CASCADE, null=True, blank=True)
    lab_room = models.ForeignKey(LabRoom, on_delete=models.CASCADE, null=True, blank=True)
    district = models.ForeignKey(District, on_delete=models.CASCADE, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE,related_name='assets', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    
    def __str__(self):
        return f"{self.name} - {self.lab_room} - {self.department}"
