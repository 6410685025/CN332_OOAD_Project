from django import forms
from .models import LostFound

class LostFoundForm(forms.ModelForm):
    class Meta:
        model = LostFound
        fields = ['item_name', 'description', 'location']
        widgets = {
            'item_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Item name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Where was it lost/found?'}),
        }
