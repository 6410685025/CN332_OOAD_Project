from django import forms
from .models import Announcement, AnnouncementAttachment

class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ['title', 'category', 'content']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Announcement Title'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        }


class AnnouncementAttachmentForm(forms.ModelForm):
    class Meta:
        model = AnnouncementAttachment
        fields = ['file']
        widgets = {
            'file': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*,.pdf,.doc,.docx,.xls,.xlsx'}),
        }
