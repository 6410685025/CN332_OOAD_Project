from django.db import models
from users.models import Resident, Technician

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
    # Technician might be null initially
    technician = models.ForeignKey(Technician, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_repairs')
    
    request_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='MAINTENANCE')
    description = models.TextField()
    location = models.CharField(max_length=255)
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
