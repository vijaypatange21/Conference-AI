from django.db import models
from events.models import Event
from attendees.models import Attendee

class Interaction(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    attendee1 = models.ForeignKey(Attendee, related_name="attendee_one", on_delete=models.CASCADE)
    attendee2 = models.ForeignKey(Attendee, related_name="attendee_two", on_delete=models.CASCADE)
    score = models.IntegerField(default=0)

    class Meta:
        unique_together = ("event", "attendee1", "attendee2")
