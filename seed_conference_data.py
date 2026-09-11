
"""
Django Management Command: seed_conference_data.py

Place this file in:

your_app/
    management/
        commands/
            seed_conference_data.py

Update the import below to match your app/models.
"""

import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker
import numpy as np

# UPDATE THESE IMPORTS
# from your_app.models import (
#     Attendee, Event, EventAttendee,
#     FaceEmbedding, EventPhoto, DetectedFace,
#     AttendeeConnection, ConnectionSharedEvent
# )

fake = Faker()

COMPANIES = [
    "OpenAI","Google","Microsoft","Amazon","Meta","Apple","NVIDIA",
    "IBM","Cisco","Oracle","Intel","Infosys","TCS","Accenture",
    "Deloitte","Zoho","Flipkart","Razorpay"
]

ROLES = [
    "Research Engineer","ML Engineer","Backend Engineer","SDE",
    "AI Consultant","Data Scientist","Student","Founder",
    "Cloud Engineer","Product Manager"
]

EVENTS = [
    "AI Summit 2026",
    "GenAI Developer Conference",
    "Cloud Expo India",
    "Startup Connect",
    "PyCon India",
    "AI HackFest",
    "ML Research Meetup",
    "Computer Vision Summit",
    "Data Science Conclave",
    "Tech Leaders Forum",
]

def embedding():
    v = np.random.normal(size=512)
    v /= np.linalg.norm(v)
    return v.tolist()

class Command(BaseCommand):
    help = "Seed Conference AI demo data"

    def handle(self,*args,**kwargs):

        self.stdout.write("Creating attendees...")

        attendees = []

        # ---- CREATE ATTENDEES ----
        for i in range(150):
            # Replace with your ORM model
            """
            attendee = Attendee.objects.create(
                name=fake.name(),
                email=f"user{i}@demo.com",
                company=random.choice(COMPANIES),
                designation=random.choice(ROLES),
                bio=fake.text(120),
            )

            FaceEmbedding.objects.create(
                attendee=attendee,
                embedding=embedding(),
                is_primary=True,
                confidence_score=0.99
            )
            attendees.append(attendee)
            """
            pass

        self.stdout.write("Creating events...")

        events=[]

        for idx,name in enumerate(EVENTS):

            start = timezone.now().date() + timedelta(days=idx*25)

            """
            event = Event.objects.create(
                name=name,
                location=fake.city(),
                start_date=start,
                end_date=start+timedelta(days=2)
            )
            events.append(event)
            """
            pass

        self.stdout.write("Registering attendees...")

        # ---- REGISTER USERS TO EVENTS ----
        """
        for event in events:

            selected=random.sample(attendees, random.randint(40,70))

            for attendee in selected:
                EventAttendee.objects.create(
                    attendee=attendee,
                    event=event,
                    role=random.choice(
                        ["Attendee","Speaker","VIP"]
                    )
                )
        """

        self.stdout.write("Creating event photos...")

        """
        for event in events:

            registered=list(
                EventAttendee.objects.filter(event=event)
            )

            for p in range(random.randint(20,35)):

                photo=EventPhoto.objects.create(
                    event=event,
                    image_url=f"photos/{event.id}_{p}.jpg",
                    processed=True
                )

                people=random.sample(
                    registered,
                    random.randint(3,8)
                )

                for person in people:

                    DetectedFace.objects.create(
                        photo=photo,
                        matched_attendee=person.attendee,
                        embedding=embedding(),
                        similarity_score=round(
                            random.uniform(.82,.99),3
                        ),
                        bbox_json={
                            "x":random.randint(0,800),
                            "y":random.randint(0,800),
                            "w":180,
                            "h":180
                        }
                    )
        """

        self.stdout.write("Building interaction graph...")

        """
        from itertools import combinations

        connection_cache={}

        for photo in EventPhoto.objects.all():

            faces=list(photo.detectedface_set.all())

            attendees=[f.matched_attendee for f in faces]

            for a,b in combinations(sorted(attendees,key=lambda x:x.id),2):

                key=(a.id,b.id)

                if key not in connection_cache:

                    conn=AttendeeConnection.objects.create(
                        attendee_a=a,
                        attendee_b=b,
                        interaction_score=1,
                        shared_photo_count=1,
                        common_event_count=0
                    )

                    connection_cache[key]=conn

                else:

                    conn=connection_cache[key]
                    conn.interaction_score+=1
                    conn.shared_photo_count+=1
                    conn.save()
        """

        self.stdout.write("Calculating common events...")

        """
        for conn in AttendeeConnection.objects.all():

            events_a=set(
                EventAttendee.objects.filter(
                    attendee=conn.attendee_a
                ).values_list("event_id",flat=True)
            )

            events_b=set(
                EventAttendee.objects.filter(
                    attendee=conn.attendee_b
                ).values_list("event_id",flat=True)
            )

            common=events_a & events_b

            conn.common_event_count=len(common)
            conn.save()

            for event_id in common:

                ConnectionSharedEvent.objects.create(
                    connection=conn,
                    event_id=event_id
                )
        """

        self.stdout.write(self.style.SUCCESS(
            "Conference demo data generated successfully!"
        ))
