from django import forms
from .models import RepairRequest
from users.models import Technician

class RepairRequestForm(forms.ModelForm):
    class Meta:
        model = RepairRequest
        fields = ['request_type', 'description', 'location']
        widgets = {
            'request_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe the issue...'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Specific location (e.g. Kitchen sink)'}),
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
        self.fields['technician'].queryset = Technician.objects.filter(is_available=True)

class UpdateRepairStatusForm(forms.ModelForm):
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
