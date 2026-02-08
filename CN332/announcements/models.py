from django.db import models
from users.models import Staff

class Announcement(models.Model):
    CATEGORY_CHOICES = (
        ('GENERAL', 'General'),
        ('EMERGENCY', 'Emergency'),
        ('MAINTENANCE', 'Maintenance'),
        ('EVENTS', 'Events'),
        ('POLICIES', 'Policies'),
    )
    
    title = models.CharField(max_length=200)
    content = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='GENERAL')
    publish_date = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, related_name='announcements')

    def __str__(self):
        return self.title


class AnnouncementAttachment(models.Model):
    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='announcements/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Attachment for {self.announcement.title}"
