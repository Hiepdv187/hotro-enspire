from django import forms
from .models import Ticket, Comments, Reply
from accounts.models import User


class CreateTicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['ticket_title','work_as', 'ticket_description', 'image','up_video', 'school', 'phone_number']
        
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
        image = self.cleaned_data.get('image')
        if image:
            # Xử lý và kiểm tra hình ảnh ở đây (kiểm tra loại, kích thước, ...)
            pass
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