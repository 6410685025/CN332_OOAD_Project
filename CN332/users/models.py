from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    contact_number = models.CharField(max_length=20, blank=True, null=True)
    profile_photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True)
    line_user_id = models.CharField(max_length=64, blank=True, null=True, unique=True)
    line_display_name = models.CharField(max_length=150, blank=True, null=True)
    line_picture_url = models.URLField(blank=True, null=True)
    line_connected_at = models.DateTimeField(blank=True, null=True)

    @property
    def is_resident(self):
        return hasattr(self, 'resident')

    @property
    def is_staff_member(self):
        return hasattr(self, 'staff')

    @property
    def is_technician(self):
        return hasattr(self, 'technician')

class Resident(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='resident')
    room_number = models.CharField(max_length=10)
    building = models.CharField(max_length=10)
    floor = models.CharField(max_length=5)

    def __str__(self):
        return f"{self.user.username} - {self.room_number}"

class Staff(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='staff')
    position = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.user.username} - {self.position}"

class Technician(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='technician')
    AVAILABILITY_CHOICES = (
        ('AVAILABLE', 'Available'),
        ('BUSY', 'Busy'),
    )
    availability = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES, default='AVAILABLE')

    def __str__(self):
        return f"{self.user.username} ({self.availability})"
