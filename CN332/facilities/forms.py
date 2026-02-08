from django import forms
from .models import Booking, Facility

class FacilityForm(forms.ModelForm):
    class Meta:
        model = Facility
        fields = ['name', 'facility_type', 'capacity', 'description', 'image']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter facility name'}),
            'facility_type': forms.Select(attrs={'class': 'form-select'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter capacity'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter description'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['facility', 'booking_date', 'time_slot']
        widgets = {
            'facility': forms.Select(attrs={'class': 'form-select'}),
            'booking_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'time_slot': forms.Select(attrs={'class': 'form-select'}, choices=[
                ('09:00-10:00', '09:00 - 10:00'),
                ('10:00-11:00', '10:00 - 11:00'),
                ('11:00-12:00', '11:00 - 12:00'),
                ('12:00-13:00', '12:00 - 13:00'),
                ('13:00-14:00', '13:00 - 14:00'),
                ('14:00-15:00', '14:00 - 15:00'),
                ('15:00-16:00', '15:00 - 16:00'),
                ('16:00-17:00', '16:00 - 17:00'),
                ('17:00-18:00', '17:00 - 18:00'),
                ('18:00-19:00', '18:00 - 19:00'),
                ('19:00-20:00', '19:00 - 20:00'),
                ('20:00-21:00', '20:00 - 21:00'),
                ('21:00-22:00', '21:00 - 22:00'),
            ]),
        }
