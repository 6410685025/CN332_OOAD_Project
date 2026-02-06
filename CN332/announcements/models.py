from django.db import models
from users.models import Staff

class Announcement(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    publish_date = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, related_name='announcements')

    def __str__(self):
        return self.title
