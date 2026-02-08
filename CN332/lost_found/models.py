from django.db import models
from users.models import Resident, Staff

class LostFound(models.Model):
    TYPE_CHOICES = (
        ('LOST', 'Lost'),
        ('FOUND', 'Found'),
    )

    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('CLAIMED', 'Claimed'),
        ('RESOLVED', 'Resolved'),
    )

    reporter = models.ForeignKey(Resident, on_delete=models.CASCADE, related_name='reported_items')
    resolver = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_items')
    claimant = models.ForeignKey(Resident, on_delete=models.SET_NULL, null=True, blank=True, related_name='claimed_items')
    item_name = models.CharField(max_length=100)
    description = models.TextField()
    location = models.CharField(max_length=255)
    item_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='LOST')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    reported_at = models.DateTimeField(auto_now_add=True)
    claimed_at = models.DateTimeField(null=True, blank=True)
    image = models.ImageField(upload_to='lost_found_images/', blank=True, null=True)
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.item_name} ({self.item_type} - {self.status})"
