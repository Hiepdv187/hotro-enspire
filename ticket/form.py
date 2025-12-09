from django import forms
from .models import Ticket, Comments, Reply
from accounts.models import User


class CreateTicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['ticket_title','work_as', 'ticket_description', 'image','up_video', 'school', 'phone_number']
    
    def clean_image(self):
        """Validate image file trước khi upload"""
        image = self.cleaned_data.get('image')
        
        if image:
            # Kiểm tra kích thước file (max 10MB)
            if image.size > 10 * 1024 * 1024:  # 10MB
                raise forms.ValidationError('Kích thước ảnh không được vượt quá 10MB')
            
            # Kiểm tra định dạng file
            allowed_formats = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
            if image.content_type not in allowed_formats:
                raise forms.ValidationError('Chỉ chấp nhận định dạng: JPG, PNG, GIF, WebP')
        
        return image
    
    def clean_up_video(self):
        """Validate video file"""
        video = self.cleaned_data.get('up_video')
        
        if video:
            # Kiểm tra kích thước file (max 100MB)
            if video.size > 100 * 1024 * 1024:  # 100MB
                raise forms.ValidationError('Kích thước video không được vượt quá 100MB')
            
            # Kiểm tra định dạng file
            allowed_formats = ['video/mp4', 'video/quicktime', 'video/x-msvideo', 'video/webm']
            if video.content_type not in allowed_formats:
                raise forms.ValidationError('Chỉ chấp nhận định dạng: MP4, MOV, AVI, WebM')
        
        return video
        
class AssignTicketForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(AssignTicketForm, self).__init__(*args, **kwargs)
        self.fields['engineer'].queryset = User.objects.filter(is_engineer=True)
        self.fields['engineer'].label_from_instance = lambda obj: f"{obj.last_name} {obj.first_name}"
        
    class Meta:
        model = Ticket
        fields = ['engineer']
    
class ChangeAssignTicketForm(forms.ModelForm):   
    class Meta:
        model = Ticket
        fields = ['engineer']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Lọc chỉ những người có vai trò is_engineer
        engineers = User.objects.filter(is_engineer=True)

        # Sử dụng label_from_instance để hiển thị tên thay vì username
        self.fields['engineer'].queryset = engineers
        self.fields['engineer'].label_from_instance = lambda obj: f"{obj.last_name} {obj.first_name}"

class CommentForm(forms.ModelForm):
    image = forms.ImageField(required=False)

    class Meta:
        model = Comments
        fields = ['body', 'image']
        widgets = {
            'body': forms.Textarea(attrs={'rows': 3}),
            'image': forms.ImageField(required=False)
        }
        labels = {
            'body': 'Bình Luận',
            'image': 'Ảnh đính kèm',
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['image'].label = 'Ảnh đính kèm(nếu có)'
    
    def clean_image(self):
        """Validate image file"""
        image = self.cleaned_data.get('image')
        
        if image:
            # Kiểm tra kích thước file (max 10MB)
            if image.size > 10 * 1024 * 1024:  # 10MB
                raise forms.ValidationError('Kích thước ảnh không được vượt quá 10MB')
            
            # Kiểm tra định dạng file
            allowed_formats = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
            if image.content_type not in allowed_formats:
                raise forms.ValidationError('Chỉ chấp nhận định dạng: JPG, PNG, GIF, WebP')
        
        return image

class ReplyForm(forms.ModelForm):
    class Meta:
        model = Reply
        fields = ['body', 'image']
        widgets = {
            'body': forms.Textarea(attrs={'rows': 1}),
        }
        labels = {
            'body': 'Trả lời bình Luận',
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['image'].label = 'Ảnh đính kèm(nếu có)'
    
    def clean_image(self):
        """Validate image file"""
        image = self.cleaned_data.get('image')
        
        if image:
            # Kiểm tra kích thước file (max 10MB)
            if image.size > 10 * 1024 * 1024:  # 10MB
                raise forms.ValidationError('Kích thước ảnh không được vượt quá 10MB')
            
            # Kiểm tra định dạng file
            allowed_formats = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
            if image.content_type not in allowed_formats:
                raise forms.ValidationError('Chỉ chấp nhận định dạng: JPG, PNG, GIF, WebP')
        
        return image
        
class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = [ 'ticket_description', 'image']
        widgets = {
            'ticket_description': forms.Textarea(attrs={'rows': 5}),
        }
        labels = {
            'ticket_description': '',
        }
    def clean_image(self):
        """Validate image file"""
        image = self.cleaned_data.get('image')
        
        if image:
            # Kiểm tra kích thước file (max 10MB)
            if image.size > 10 * 1024 * 1024:  # 10MB
                raise forms.ValidationError('Kích thước ảnh không được vượt quá 10MB')
            
            # Kiểm tra định dạng file
            allowed_formats = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
            if image.content_type not in allowed_formats:
                raise forms.ValidationError('Chỉ chấp nhận định dạng: JPG, PNG, GIF, WebP')
        
        return image
    
class AdminCreateTicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['ticket_title','work_as','engineer','ticket_description', 'image','up_video', 'school', 'phone_number']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Lọc chỉ những người có vai trò is_engineer
        engineers = User.objects.filter(is_engineer=True)

        # Sử dụng label_from_instance để hiển thị tên thay vì username
        self.fields['engineer'].queryset = engineers
        self.fields['engineer'].label_from_instance = lambda obj: f"{obj.last_name} {obj.first_name}"
        
        # Bắt buộc phải chọn engineer
        self.fields['engineer'].required = True
        self.fields['engineer'].empty_label = "-- Chọn người xử lý --"