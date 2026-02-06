from django.db import models
from users.models import Resident, Staff

class LostFound(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('RESOLVED', 'Resolved'),
    )

    reporter = models.ForeignKey(Resident, on_delete=models.CASCADE, related_name='reported_items')
    resolver = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_items')
    item_name = models.CharField(max_length=100)
    description = models.TextField()
    location = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    reported_at = models.DateTimeField(auto_now_add=True)
    # image = models.ImageField(upload_to='lost_found_images/', blank=True, null=True) # Requires Pillow

    def __str__(self):
        return f"{self.item_name} ({self.status})"
