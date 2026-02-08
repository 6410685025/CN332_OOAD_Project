from django.db import models
from django.core.validators import FileExtensionValidator
from users.models import Resident, Technician, Staff

class RepairRequest(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('ON_PROCESS', 'On Process'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    )
    TYPE_CHOICES = (
        ('MAINTENANCE', 'Maintenance'),
        ('COMPLAINT', 'Complaint'),
    )

    resident = models.ForeignKey(Resident, on_delete=models.CASCADE, related_name='repair_requests')
    # Technician for maintenance requests
    technician = models.ForeignKey(Technician, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_repairs')
    # Staff for complaint requests
    assigned_staff = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_complaints')
    
    request_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='MAINTENANCE')
    description = models.TextField()
    location = models.CharField(max_length=255)
    location_description = models.TextField(blank=True, null=True, help_text="Additional details about the location (e.g., 'Left side of the door', 'Third floor window')")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    rating = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.request_type} - {self.location} ({self.status})"

class WorkLog(models.Model):
    repair_request = models.ForeignKey(RepairRequest, on_delete=models.CASCADE, related_name='logs')
    description = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Log {self.id} for Request {self.repair_request.id}"


class RepairImage(models.Model):
    IMAGE_TYPE_CHOICES = (
        ('BEFORE', 'Before'),
        ('AFTER', 'After'),
    )

    repair_request = models.ForeignKey(RepairRequest, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(
        upload_to='repair_images/',
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'webp'])]
    )
    image_type = models.CharField(max_length=10, choices=IMAGE_TYPE_CHOICES, default='BEFORE')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField(blank=True, null=True, help_text="Optional description of the image")

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.image_type} image for Request {self.repair_request.id}"
