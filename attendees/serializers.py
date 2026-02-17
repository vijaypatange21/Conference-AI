"""
attendees/serializers.py

DRF serializers for Attendee endpoints.

Design:
- AttendeeJoinSerializer: POST /events/join (create attendee + selfie)
- AttendeeDetailSerializer: GET /attendees/{id}
- AttendeeSelfieUploadSerializer: POST /attendees/upload-selfie
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from attendees.models import Attendee
from events.models import Event


class AttendeeJoinSerializer(serializers.Serializer):
    """
    Join an event (create Attendee + upload selfie).
    
    POST /events/join
    
    Accepts:
    - event_code: UUID code of event to join
    - selfie: Image file
    - first_name, last_name: User info
    - email: User email
    
    Returns: Attendee details with user info
    """
    
    event_code = serializers.CharField(required=True)
    selfie = serializers.ImageField(required=True)
    first_name = serializers.CharField(max_length=150, required=False)
    last_name = serializers.CharField(max_length=150, required=False)
    email = serializers.EmailField(required=False)
    
    def validate_event_code(self, value):
        """Verify event exists."""
        try:
            Event.objects.get(code=value)
        except Event.DoesNotExist:
            raise serializers.ValidationError("Event not found")
        return value
    
    def create(self, validated_data):
        """
        Create User + Attendee + upload selfie.
        Signal will auto-generate embedding.
        """
        # Extract data
        event_code = validated_data.pop('event_code')
        selfie = validated_data.pop('selfie')
        first_name = validated_data.pop('first_name', '')
        last_name = validated_data.pop('last_name', '')
        email = validated_data.pop('email', '')
        
        # Create user (username = email or UUID)
        import uuid
        username = email or f"attendee_{uuid.uuid4().hex[:8]}"
        
        user = User.objects.create_user(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name
        )
        
        # Create attendee with selfie
        event = Event.objects.get(code=event_code)
        attendee = Attendee.objects.create(
            user=user,
            event=event,
            selfie=selfie
        )
        
        return attendee


class AttendeeDetailSerializer(serializers.ModelSerializer):
    """
    Attendee details.
    GET /attendees/{id}
    """
    
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    event_id = serializers.IntegerField(read_only=True)
    event_name = serializers.CharField(source='event.name', read_only=True)
    embedding_ready = serializers.SerializerMethodField()
    
    class Meta:
        model = Attendee
        fields = [
            'id', 'user_id', 'username', 'email',
            'event_id', 'event_name', 'selfie',
            'embedding_ready', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_embedding_ready(self, obj):
        """Check if embedding has been generated."""
        return obj.embedding is not None


class AttendeeSelfieUploadSerializer(serializers.Serializer):
    """
    Upload selfie for existing attendee.
    
    POST /attendees/update-selfie
    
    Accepts:
    - selfie: Image file (replaces current)
    
    Why separate endpoint:
    - Allows attendee to update selfie
    - Signal will regenerate embedding
    """
    
    selfie = serializers.ImageField(required=True)
    
    def update(self, instance, validated_data):
        """Update attendee selfie."""
        instance.selfie = validated_data['selfie']
        instance.save(update_fields=['selfie'])
        return instance
