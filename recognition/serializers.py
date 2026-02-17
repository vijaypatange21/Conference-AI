"""
recognition/serializers.py

DRF serializers for EventImage and DetectedFace.

Design:
- EventImageUploadSerializer: POST /events/upload-image
- DetectedFaceSerializer: Nested in response, shows matched attendee
"""

from rest_framework import serializers
from recognition.models import EventImage, DetectedFace
from events.models import Event
from attendees.serializers import AttendeeDetailSerializer


class EventImageUploadSerializer(serializers.ModelSerializer):
    """
    Upload image for event.
    
    POST /events/{event_id}/upload-image
    
    Trigger:
    - Signal queues Celery task to detect faces
    - Response returns immediately (async processing)
    - Later: Poll /events/{event_id}/images to see results
    """
    
    event_id = serializers.IntegerField(write_only=True)
    status = serializers.SerializerMethodField()
    
    class Meta:
        model = EventImage
        fields = ['id', 'event_id', 'image', 'uploaded_at', 'status']
        read_only_fields = ['id', 'uploaded_at']
    
    def validate_event_id(self, value):
        """Verify event exists."""
        try:
            Event.objects.get(id=value)
        except Event.DoesNotExist:
            raise serializers.ValidationError("Event not found")
        return value
    
    def create(self, validated_data):
        """Create EventImage (signal will handle processing)."""
        event_id = validated_data.pop('event_id')
        event = Event.objects.get(id=event_id)
        
        event_image = EventImage.objects.create(
            event=event,
            image=validated_data['image']
        )
        
        return event_image
    
    def get_status(self, obj):
        """Show number of faces detected."""
        face_count = obj.detectedface_set.count()
        matched_count = obj.detectedface_set.filter(
            matched_attendee__isnull=False
        ).count()
        
        return {
            'total_faces': face_count,
            'matched_faces': matched_count,
            'processing': face_count == 0  # Still processing if no faces detected
        }


class DetectedFaceSerializer(serializers.ModelSerializer):
    """
    Detected face details with matched attendee.
    Nested in EventImage response.
    """
    
    matched_attendee = AttendeeDetailSerializer(read_only=True)
    
    class Meta:
        model = DetectedFace
        fields = ['id', 'image', 'matched_attendee', 'embedding']


class EventImageDetailSerializer(serializers.ModelSerializer):
    """
    Event image with all detected faces.
    GET /events/{event_id}/images/{image_id}
    """
    
    detected_faces = DetectedFaceSerializer(
        source='detectedface_set',
        many=True,
        read_only=True
    )
    matched_attendees = serializers.SerializerMethodField()
    
    class Meta:
        model = EventImage
        fields = [
            'id', 'event', 'image', 'uploaded_at',
            'detected_faces', 'matched_attendees'
        ]
    
    def get_matched_attendees(self, obj):
        """Get unique attendees matched in this image."""
        from attendees.models import Attendee
        attendees = Attendee.objects.filter(
            detectedface__image=obj,
            detectedface__matched_attendee__isnull=False
        ).distinct()
        
        return AttendeeDetailSerializer(attendees, many=True).data
