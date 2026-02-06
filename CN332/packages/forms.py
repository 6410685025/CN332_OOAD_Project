from django import forms
from .models import Package
from users.models import Resident

class PackageForm(forms.ModelForm):
    class Meta:
        model = Package
        fields = ['resident', 'sender']
        widgets = {
            'resident': forms.Select(attrs={'class': 'form-select'}),
            'sender': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Sender name (e.g. Lazada, Shopee)'}),
        }
