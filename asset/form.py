from .models import Department, Asset, District, School, LabRoom
from django import forms

class CreateDepartmentForm(forms.ModelForm):
    class Meta:
        model= Department
        fields = ['name']

class CreateAssetDepartmentForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = ['name', 'asset_amount', 'asset_status']
        widgets = {
            'asset_amount': forms.NumberInput(attrs={'min': 1, 'value': 1}),
        }
        
class UpdateAssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = ['asset_amount']

class AssetSplitForm(forms.Form):
    asset_amount = forms.IntegerField(min_value=1)
    asset_id = forms.IntegerField(widget=forms.HiddenInput, required=False)

    def clean_asset_amount(self):
        asset_amount = self.cleaned_data['asset_amount']
        return asset_amount
    
    def clean(self):
        cleaned_data = super().clean()
        asset_id = cleaned_data.get('asset_id')
        # Thêm các điều kiện kiểm tra nếu cần cho asset_id ở đây
        return cleaned_data
    
class CreateDistrictForm(forms.ModelForm):
    class Meta:
        model = District
        fields = ['name']
        
class CreateAssetDistrictForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = ['name', 'asset_amount', 'asset_status']
        
class CreateSchoolForm(forms.ModelForm):
    class Meta:
        model = School
        fields = ['name', 'school_status', 'school_address', 'school_location']
        
class UpdateSchoolForm(forms.ModelForm):
    class Meta:
        model = School
        fields = ['name', 'school_status']
        
class CreateLabRoomForm(forms.ModelForm):
    class Meta:
        model = LabRoom
        fields = ['name']
        
class CreateAssetLabRoomForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = ['name', 'asset_amount', 'asset_status', 'lab_room']
        widgets = {'lab_room': forms.HiddenInput()}
        
class EditAssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = ['name', 'asset_amount']
        widgets = {'lab_room': forms.HiddenInput()}
        
class MoveAssetForm(forms.ModelForm):
    new_department = forms.ModelChoiceField(queryset=Department.objects.all(), label='Chọn phòng ban', required=False)
    new_district = forms.ModelChoiceField(queryset=District.objects.all(), label='Chọn Quận', required=False)
    new_school = forms.ModelChoiceField(queryset=School.objects.all(), label='Chọn trường', required=False)
    new_labroom = forms.ModelChoiceField(queryset=LabRoom.objects.all(), label='Chọn phòng lab', required=False)
    quantity = forms.IntegerField(label='Số lượng', min_value=1)

    class Meta:
        model = Asset
        fields = ['new_department', 'new_district', 'new_school', 'new_labroom', 'quantity']
