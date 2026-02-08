from django import forms
from .models import RepairRequest, RepairImage
from users.models import Technician, Staff

class RepairRequestForm(forms.ModelForm):
    class Meta:
        model = RepairRequest
        fields = ['request_type', 'location', 'location_description', 'description']
        widgets = {
            'request_type': forms.Select(attrs={'class': 'form-select'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Lat: 13.735..., Lng: 100.501...', 'readonly': True}),
            'location_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'E.g., "Left side of the door", "Third floor window", "Kitchen sink area"'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe the issue...'}),
        }


class RepairImageForm(forms.ModelForm):
    class Meta:
        model = RepairImage
        fields = ['image', 'image_type', 'description']
        widgets = {
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'data-max-size': '5242880'  # 5MB in bytes
            }),
            'image_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Optional: Describe what is shown in the image'
            }),
        }

class AssignTechnicianForm(forms.ModelForm):
    class Meta:
        model = RepairRequest
        fields = ['technician']
        widgets = {
            'technician': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['technician'].queryset = Technician.objects.filter(availability='AVAILABLE')
        self.fields['technician'].label = 'Select Technician'

class AssignStaffForm(forms.ModelForm):
    class Meta:
        model = RepairRequest
        fields = ['assigned_staff']
        widgets = {
            'assigned_staff': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['assigned_staff'].queryset = Staff.objects.all()
        self.fields['assigned_staff'].label = 'Select Staff Member'

class UpdateRepairStatusForm(forms.ModelForm):
    class Meta:
        model = RepairRequest
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

class UpdateComplaintStatusForm(forms.ModelForm):
    work_note = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Add a note about your work or response...'
        }),
        required=False,
        label='Work Note'
    )
    
    class Meta:
        model = RepairRequest
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

class RatingForm(forms.Form):
    rating = forms.ChoiceField(
        choices=[(i, f'{i} ⭐') for i in range(1, 6)],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
