from django.db import models
from django.contrib.auth.models import User
from pgvector.django import VectorField
from events.models import Event

class Attendee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    selfie = models.ImageField(upload_to="selfies/")
    embedding = VectorField(dimensions=512, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.event.name}"
