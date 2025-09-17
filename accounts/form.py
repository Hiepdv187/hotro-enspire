from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from django import forms
from django.contrib.auth.forms import UserChangeForm
from .models import User
import re
from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from django.core.exceptions import ValidationError

User = get_user_model()

class RegisterCustomerForm(UserCreationForm):
    class Meta:
        model = User
        fields = [ 'first_name','last_name', 'email','work_place', 'school', 'password1', 'password2']
    def clean(self):
        if not isinstance(self.cleaned_data, dict):
            raise forms.ValidationError('Lỗi')
        
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        
        if password1 and password2 and password1 == password2:
            return self.cleaned_data
        raise forms.ValidationError('\n 2 mật khẩu không trùng khớp')
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            raise forms.ValidationError('Không đúng định dạng Email')
        try:
            User.objects.get(email=email)
        except ObjectDoesNotExist:
            return email
        raise forms.ValidationError('Email đã tồn tại')
    
class CustomUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['avatar']


    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        width = 50  # Đặt kích thước bạn muốn
        height = 50
        self.instance.resize_avatar(width, height)
        
    def value_from_datadict(self, data, files, name):
        return files.get(name)

class UserProfileForm(UserChangeForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'work_place','phone', 'first_name','last_name', 'title', 'avatar', 'school', 'date_of_birth', 'gender')
        widgets = {
            'avatar': CustomUserForm(),
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email','phone', 'work_place', 'first_name','last_name', 'title', 'avatar', 'school', 'date_of_birth', 'gender']
        widgets = {
            'avatar': forms.FileInput(),
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].disabled = True
        self.fields['email'].widget.attrs['class'] = 'form-control text-secondary'
        
        # Nếu bạn muốn username không được gửi đi (POST) để tránh thay đổi giá trị
        self.fields['email'].required = False

    def clean_username(self):
        # Giữ lại giá trị username cũ
        return self.instance.email
        
class CustomPasswordChangeForm(PasswordChangeForm):
    new_password1 = forms.CharField(
        label="New password",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        strip=False,
        help_text="Enter your new password."
    )
    new_password2 = forms.CharField(
        label="Confirm new password",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text="Enter the same password as before, for verification."
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

    def clean_new_password1(self):
        new_password1 = self.cleaned_data.get('new_password1')
        if len(new_password1) < 6:
            raise ValidationError("The new password must be at least 6 characters long.")
        return new_password1
