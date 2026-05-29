from django.db import models
import uuid

class Event(models.Model):
    name = models.CharField(max_length=255)
    event_code = models.UUIDField(default=uuid.uuid4, unique=True)
    location = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    start_date = models.DateTimeField(default=None, null=True, blank=True)
    end_date = models.DateTimeField(default=None, null=True, blank=True)
    def __str__(self):
        return self.name
