"""
attendees/views.py

REST API views for attendees.

Endpoints:
- POST /events/join -> Join event (create attendee + selfie)
- GET /attendees/{id} -> Attendee details
- PATCH /attendees/{id}/update-selfie -> Update selfie
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from attendees.models import Attendee
from attendees.serializers import (
    AttendeeJoinSerializer,
    AttendeeDetailSerializer,
    AttendeeSelfieUploadSerializer
)
from events.models import Event


class AttendeeJoinViewSet(viewsets.ViewSet):
    """
    Join an event as a new attendee.
    
    POST /events/join
    Body:
    {
        "event_code": "550e8400-e29b-41d4-a716-446655440000",
        "selfie": <image file>,
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@example.com"
    }
    
    Returns: New Attendee details + User info
    """
    
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def join(self, request):
        """Join event with selfie."""
        serializer = AttendeeJoinSerializer(data=request.data)
        if serializer.is_valid():
            attendee = serializer.save()
            response_serializer = AttendeeDetailSerializer(attendee)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AttendeeViewSet(viewsets.ModelViewSet):
    """
    Attendee management.
    
    GET    /attendees/{id}           -> Attendee details
    PATCH  /attendees/{id}/update-selfie -> Update selfie
    """
    
    queryset = Attendee.objects.select_related('user', 'event')
    serializer_class = AttendeeDetailSerializer
    permission_classes = [AllowAny]
    
    @action(detail=True, methods=['patch'], permission_classes=[AllowAny])
    def update_selfie(self, request, pk=None):
        """
        Update attendee's selfie.
        
        PATCH /attendees/{id}/update-selfie
        Body: {selfie: file}
        
        This will trigger signal to regenerate embedding.
        """
        
        attendee = self.get_object()
        serializer = AttendeeSelfieUploadSerializer(
            attendee,
            data=request.data,
            partial=True
        )
        
        if serializer.is_valid():
            serializer.save()
            response_serializer = AttendeeDetailSerializer(attendee)
            return Response(response_serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
