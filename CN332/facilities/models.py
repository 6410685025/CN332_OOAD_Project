from django.db import models
from users.models import Resident

class Facility(models.Model):
    TYPE_CHOICES = (
        ('SWIMMING_POOL', 'Swimming Pool'),
        ('GYM', 'Gym'),
        ('MEETING_ROOM', 'Meeting Room'),
        ('PLAYGROUND', 'Playground'),
    )
    
    name = models.CharField(max_length=100)
    facility_type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    capacity = models.IntegerField()
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='facility_images/', blank=True, null=True)
    is_open = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.get_facility_type_display()})"

class Booking(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('CANCELLED', 'Cancelled'),
        ('EXPIRED', 'Expired'),
    )

    resident = models.ForeignKey(Resident, on_delete=models.CASCADE, related_name='bookings')
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name='bookings')
    booking_date = models.DateField()
    time_slot = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Booking {self.id} - {self.resident} @ {self.facility}"
