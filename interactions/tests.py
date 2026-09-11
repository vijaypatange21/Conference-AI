from django.test import TestCase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status
from events.models import Event
from attendees.models import Attendee
from interactions.models import Interaction


class MyConnectionsAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        # Create an event
        self.event = Event.objects.create(name="Networking Gala")
        
        # Create selfie file
        self.dummy_selfie = SimpleUploadedFile(
            name='selfie.jpg',
            content=b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x05\x04\x04\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b', # 1x1 gif
            content_type='image/gif'
        )

        # Create primary attendee
        self.user1 = User.objects.create_user(
            username="john_doe",
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            password="testpassword123"
        )
        self.attendee1 = Attendee.objects.create(
            user=self.user1,
            event=self.event,
            selfie=self.dummy_selfie
        )

        # Create connection 1
        self.user2 = User.objects.create_user(
            username="alice",
            first_name="Alice",
            last_name="Johnson",
            email="alice@example.com",
            password="testpassword123"
        )
        self.attendee2 = Attendee.objects.create(
            user=self.user2,
            event=self.event,
            selfie=self.dummy_selfie
        )

        # Create connection 2
        self.user3 = User.objects.create_user(
            username="bob",
            first_name="Bob",
            last_name="Smith",
            email="bob@example.com",
            password="testpassword123"
        )
        self.attendee3 = Attendee.objects.create(
            user=self.user3,
            event=self.event,
            selfie=self.dummy_selfie
        )

        # Create interactions with specific scores to test sorting
        self.interaction1 = Interaction.objects.create(
            event=self.event,
            attendee1=self.attendee1,
            attendee2=self.attendee3, # bob
            interaction_score=50
        )
        self.interaction2 = Interaction.objects.create(
            event=self.event,
            attendee1=self.attendee1,
            attendee2=self.attendee2, # alice
            interaction_score=95
        )

    def test_my_connections_format_and_ordering(self):
        url = "/api/interactions/my_connections/"
        response = self.client.get(url, {"attendee_id": self.attendee1.id, "event_id": self.event.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify outer structure
        data = response.json()
        self.assertIn("attendee", data)
        self.assertIn("connections", data)
        self.assertIn("total_connections", data)
        
        self.assertEqual(data["total_connections"], 2)
        
        # Verify connections payload and ordering (alice has 95, bob has 50, so alice should be first)
        connections = data["connections"]
        self.assertEqual(len(connections), 2)
        
        # 1. First connection (Alice - 95 score)
        conn1 = connections[0]
        self.assertEqual(conn1["id"], self.interaction2.id)
        self.assertEqual(conn1["interaction_score"], 95)
        self.assertIn("connected_attendee", conn1)
        
        ca1 = conn1["connected_attendee"]
        self.assertEqual(ca1["id"], self.attendee2.id)
        self.assertEqual(ca1["username"], "alice")
        self.assertEqual(ca1["first_name"], "Alice")
        self.assertEqual(ca1["last_name"], "Johnson")
        self.assertEqual(ca1["email"], "alice@example.com")
        self.assertIsNotNone(ca1["selfie"])
        
        # 2. Second connection (Bob - 50 score)
        conn2 = connections[1]
        self.assertEqual(conn2["id"], self.interaction1.id)
        self.assertEqual(conn2["interaction_score"], 50)
        self.assertIn("connected_attendee", conn2)
        
        ca2 = conn2["connected_attendee"]
        self.assertEqual(ca2["id"], self.attendee3.id)
        self.assertEqual(ca2["username"], "bob")
        self.assertEqual(ca2["first_name"], "Bob")
        self.assertEqual(ca2["last_name"], "Smith")
        self.assertEqual(ca2["email"], "bob@example.com")
        self.assertIsNotNone(ca2["selfie"])

    def test_query_count_optimization(self):
        url = "/api/interactions/my_connections/"
        
        # With optimization, it should execute exactly 2 queries:
        # 1. Get primary attendee by ID
        # 2. Select interactions with all related tables joined
        with self.assertNumQueries(2):
            response = self.client.get(url, {"attendee_id": self.attendee1.id, "event_id": self.event.id})
            self.assertEqual(response.status_code, status.HTTP_200_OK)
