from django import forms
from .models import LostFound

class LostFoundForm(forms.ModelForm):
    class Meta:
        model = LostFound
        fields = ['item_type', 'item_name', 'description', 'location', 'image']
        widgets = {
            'item_type': forms.Select(attrs={'class': 'form-select'}),
            'item_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Item name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Where was it lost/found?'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
