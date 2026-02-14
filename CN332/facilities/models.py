from django.db import models
from django.utils import timezone
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
    confirmation_token = models.CharField(max_length=64, blank=True, null=True)
    confirmation_deadline = models.DateTimeField(blank=True, null=True)
    reminder_sent_at = models.DateTimeField(blank=True, null=True)
    confirmed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Booking {self.id} - {self.resident} @ {self.facility}"

    def get_start_end_datetimes(self):
        start_str, end_str = self.time_slot.split('-')
        start_hour, start_minute = [int(value) for value in start_str.split(':')]
        end_hour, end_minute = [int(value) for value in end_str.split(':')]

        tz = timezone.get_current_timezone()
        start_dt = timezone.make_aware(
            timezone.datetime.combine(self.booking_date, timezone.datetime.min.time()).replace(
                hour=start_hour,
                minute=start_minute,
            ),
            timezone=tz,
        )
        end_dt = timezone.make_aware(
            timezone.datetime.combine(self.booking_date, timezone.datetime.min.time()).replace(
                hour=end_hour,
                minute=end_minute,
            ),
            timezone=tz,
        )
        return start_dt, end_dt
