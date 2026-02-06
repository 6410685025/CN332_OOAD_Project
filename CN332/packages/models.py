from django.db import models
from users.models import Resident, Staff

class Package(models.Model):
    STATUS_CHOICES = (
        ('RECEIVED', 'Received'),
        ('PICKED_UP', 'Picked Up'),
    )

    resident = models.ForeignKey(Resident, on_delete=models.CASCADE, related_name='packages')
    # Staff who received it into the system
    handled_by = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, related_name='handled_packages')
    sender = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='RECEIVED')
    arrived_at = models.DateTimeField(auto_now_add=True)
    picked_up_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Package for {self.resident.room_number} from {self.sender}"
