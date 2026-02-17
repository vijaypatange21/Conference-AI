"""
events/views.py

REST API views for events.

Endpoints:
- POST /events/create -> Create event
- GET /events -> List events
- GET /events/{id} -> Event details
- POST /events/{id}/upload-image -> Upload event image
- GET /events/{id}/images -> List event images

Why thin views:
- Business logic is in services/ modules
- Views only handle HTTP request/response mapping
- Easy to test services independently
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from events.models import Event
from events.serializers import (
    EventCreateSerializer,
    EventDetailSerializer,
    EventListSerializer
)
from recognition.models import EventImage
from recognition.serializers import (
    EventImageUploadSerializer,
    EventImageDetailSerializer
)
from attendees.serializers import (
    AttendeeJoinSerializer,
    AttendeeDetailSerializer
)


class EventViewSet(viewsets.ModelViewSet):
    """
    Event management.
    
    POST   /events/create      -> Create new event
    GET    /events             -> List all events
    GET    /events/{id}        -> Event details
    POST   /events/{id}/upload-image -> Upload image to event
    GET    /events/{id}/images -> List event images
    """
    
    queryset = Event.objects.all().order_by('-created_at')
    permission_classes = [AllowAny]
    
    def get_serializer_class(self):
        """Use appropriate serializer based on action."""
        if self.action == 'create':
            return EventCreateSerializer
        elif self.action == 'retrieve':
            return EventDetailSerializer
        elif self.action == 'list':
            return EventListSerializer
        return EventCreateSerializer
    
    @action(detail=True, methods=['post'], permission_classes=[AllowAny])
    def upload_image(self, request, pk=None):
        """
        Upload event image.
        
        POST /events/{id}/upload-image
        Body: {image: file}
        
        Returns: Image details + processing status
        
        Why separate action:
        - Clear URL structure
        - Handled by different serializer
        - Can have different permissions
        """
        
        event = self.get_object()
        
        serializer = EventImageUploadSerializer(
            data={'event_id': event.id, 'image': request.FILES.get('image')}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'], permission_classes=[AllowAny])
    def images(self, request, pk=None):
        """
        List all images for an event.
        
        GET /events/{id}/images
        
        Returns: Array of EventImage with detection status
        """
        
        event = self.get_object()
        images = EventImage.objects.filter(event=event).order_by('-uploaded_at')
        
        serializer = EventImageDetailSerializer(images, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def join(self, request):
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
        serializer = AttendeeJoinSerializer(data=request.data)
        if serializer.is_valid():
            attendee = serializer.save()
            response_serializer = AttendeeDetailSerializer(attendee)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

