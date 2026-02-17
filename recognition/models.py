from django.db import models
from pgvector.django import VectorField
from events.models import Event
from attendees.models import Attendee

class EventImage(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    image = models.ImageField(upload_to="event_images/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

class DetectedFace(models.Model):
    image = models.ForeignKey(EventImage, on_delete=models.CASCADE)
    embedding = VectorField(dimensions=512)
    matched_attendee = models.ForeignKey(
        Attendee,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )
