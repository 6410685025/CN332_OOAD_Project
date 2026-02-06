from django import forms
from .models import Booking, Facility

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
                ('13:00-14:00', '13:00 - 14:00'),
                ('14:00-15:00', '14:00 - 15:00'),
                ('15:00-16:00', '15:00 - 16:00'),
                ('16:00-17:00', '16:00 - 17:00'),
            ]),
        }
