"""
interactions/serializers.py

DRF serializers for Interaction endpoints.

Design:
- InteractionDetailSerializer: Shows connected attendee info + score
- Used in GET /interactions/my-connections
"""

from rest_framework import serializers
from interactions.models import Interaction
from attendees.serializers import AttendeeDetailSerializer


class InteractionDetailSerializer(serializers.ModelSerializer):
    """
    Show interaction score between two attendees.
    
    GET /interactions/my-connections returns list of these.
    """
    
    # Use SerializerMethodField to dynamically show the "other" attendee
    connected_attendee = serializers.SerializerMethodField()
    
    class Meta:
        model = Interaction
        fields = ['id', 'event', 'connected_attendee', 'score']
        read_only_fields = ['id', 'event', 'score']
    
    def get_connected_attendee(self, obj):
        """Return the attendee that is NOT the current user."""
        request = self.context.get('request')
        if not request or not request.user:
            return None
        
        # Determine which attendee is the "other" one
        current_user_attendee = getattr(request, 'current_attendee', None)
        if not current_user_attendee:
            return None
        
        if obj.attendee1_id == current_user_attendee.id:
            other = obj.attendee2
        else:
            other = obj.attendee1
        
        return AttendeeDetailSerializer(other).data


class InteractionListSerializer(serializers.ModelSerializer):
    """
    Simple interaction view for listing.
    """
    
    attendee1_username = serializers.CharField(source='attendee1.user.username', read_only=True)
    attendee2_username = serializers.CharField(source='attendee2.user.username', read_only=True)
    
    class Meta:
        model = Interaction
        fields = ['id', 'event', 'attendee1_username', 'attendee2_username', 'score']
