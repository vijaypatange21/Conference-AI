"""
recognition/views.py

REST API views for face recognition results.

Endpoints:
- GET /events/{event_id}/detected-faces -> List all detected faces in event
- GET /detected-faces/{id} -> Face details
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from recognition.models import EventImage, DetectedFace
from recognition.serializers import (
    EventImageDetailSerializer,
    DetectedFaceSerializer
)
from events.models import Event


class DetectedFaceViewSet(viewsets.ModelViewSet):
    """
    Query detected faces and their matches.
    
    GET    /detected-faces            -> List all detected faces
    GET    /detected-faces/{id}       -> Face details
    GET    /events/{id}/detected-faces -> Faces in specific event
    """
    
    queryset = DetectedFace.objects.select_related(
        'image',
        'matched_attendee',
        'image__event'
    ).order_by('-image__uploaded_at')
    
    serializer_class = DetectedFaceSerializer
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def by_event(self, request):
        """
        List all detected faces in a specific event.
        
        GET /detected-faces/by_event?event_id=1
        
        Query params:
        - event_id: ID of event to filter by
        - matched_only: If true, only show matched faces
        """
        
        event_id = request.query_params.get('event_id')
        matched_only = request.query_params.get('matched_only', 'false').lower() == 'true'
        
        if not event_id:
            return Response(
                {'error': 'event_id parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            return Response(
                {'error': 'Event not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        faces = DetectedFace.objects.filter(image__event=event)
        
        if matched_only:
            faces = faces.exclude(matched_attendee__isnull=True)
        
        serializer = self.get_serializer(faces, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def stats(self, request):
        """
        Recognition statistics.
        
        GET /detected-faces/stats
        
        Returns:
        - total_faces: Total faces detected
        - total_matched: Faces with matches
        - match_rate: Percentage of successful matches
        - by_event: Breakdown by event
        """
        
        from django.db.models import Count, Q
        
        total_faces = DetectedFace.objects.count()
        total_matched = DetectedFace.objects.exclude(matched_attendee__isnull=True).count()
        
        match_rate = (total_matched / total_faces * 100) if total_faces > 0 else 0
        
        # Stats by event
        event_stats = []
        for event in Event.objects.annotate(
            face_count=Count('eventimage__detectedface')
        ):
            matched = DetectedFace.objects.filter(
                image__event=event,
                matched_attendee__isnull=False
            ).count()
            
            event_stats.append({
                'event_id': event.id,
                'event_name': event.name,
                'total_faces': event.eventimage_set.count(),
                'matched_faces': matched,
                'match_rate': (matched / event.eventimage_set.count() * 100) if event.eventimage_set.count() > 0 else 0
            })
        
        return Response({
            'total_faces': total_faces,
            'total_matched': total_matched,
            'match_rate': f"{match_rate:.1f}%",
            'by_event': event_stats
        })
