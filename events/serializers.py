"""
events/serializers.py

DRF serializers for Event endpoints.

Design:
- EventCreateSerializer: Simple, for POST /events/create
- EventDetailSerializer: Rich, includes attendee info
"""

from rest_framework import serializers
from events.models import Event


class EventCreateSerializer(serializers.ModelSerializer):
    """
    Create new event.
    POST /events/create
    """
    
    class Meta:
        model = Event
        fields = ['id', 'name', 'code', 'created_at']
        read_only_fields = ['id', 'code', 'created_at']
    
    def create(self, validated_data):
        """Create event with auto-generated UUID code."""
        event = Event.objects.create(**validated_data)
        return event


class EventDetailSerializer(serializers.ModelSerializer):
    """
    Event details including attendee count.
    GET /events/{id}
    """
    
    attendee_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Event
        fields = ['id', 'name', 'code', 'created_at', 'attendee_count']
        read_only_fields = ['id', 'code', 'created_at']
    
    def get_attendee_count(self, obj):
        """Count attendees with embeddings (ready for matching)."""
        from attendees.models import Attendee
        return Attendee.objects.filter(
            event=obj,
            embedding__isnull=False
        ).count()


class EventListSerializer(serializers.ModelSerializer):
    """
    List events with basic info.
    GET /events
    """
    
    class Meta:
        model = Event
        fields = ['id', 'name', 'code', 'created_at']
